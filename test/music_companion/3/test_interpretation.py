import json
import math
import struct
import wave
from pathlib import Path
from uuid import uuid4

import pytest

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import BlueprintRevision
from application.creation_service import DemoCreationRecord, DemoCreationStore, DemoMusicVersion
from music_companion.interpretation import interpret_audio_artifact, resolve_creation_context
from music_companion.schema import (
    AcousticFeatures,
    AudioAnalysisResult,
    AudioTimeSegment,
    FeatureStatistics,
    MusicSemanticAnalysisResult,
    SemanticLabelScore,
    SemanticTimeSegment,
)
from music_engine.audio_store import AudioStore
from music_engine.schema import AceStepGenerationResult, MusicGenerationSpec


def _blueprint() -> MusicBlueprint:
    return MusicBlueprint(
        primary_emotion="joy",
        secondary_emotions=[],
        energy=0.7,
        valence=0.9,
        tempo=100,
        key="C Major",
        instruments=["piano", "strings", "bass"],
        texture="bright",
        scene="sunny_afternoon",
        progression="gentle_to_bright",
    )


def _wav_bytes(path: Path) -> bytes:
    sample_rate = 8_000
    frames = bytearray()
    for index in range(1_600):
        value = int(6_000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        frames.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(frames)
    return path.read_bytes()


def _artifact(tmp_path: Path, *, revision_id=None):
    source = tmp_path / "source.wav"
    content = _wav_bytes(source)
    store = AudioStore(tmp_path / "data")
    artifact = store.save(
        draft_id=uuid4(),
        revision_id=revision_id or uuid4(),
        generation_spec=MusicGenerationSpec(
            caption="bright instrumental music with piano, strings, and bass",
            bpm=100,
            key="C Major",
        ),
        generation_result=AceStepGenerationResult(
            task_id="interpretation-test",
            audio_bytes=content,
            content_type="audio/wav",
        ),
    )
    return store, artifact, content


def _analysis_results(artifact_id):
    stats = FeatureStatistics(mean=0.1, minimum=0.01, maximum=0.2, standard_deviation=0.02)
    acoustic = AudioAnalysisResult(
        audio_artifact_id=artifact_id,
        source_name=f"{artifact_id}.wav",
        duration_seconds=0.2,
        sample_rate_hz=8_000,
        channels=1,
        tempo_bpm_estimate=100,
        acoustic_features=AcousticFeatures(
            rms_amplitude=stats,
            spectral_centroid_hz=FeatureStatistics(
                mean=2_000, minimum=1_000, maximum=3_000, standard_deviation=200
            ),
            onset_strength=stats,
            onset_count=3,
        ),
        time_segments=(AudioTimeSegment(
            start_seconds=0,
            end_seconds=0.2,
            rms_amplitude=0.1,
            spectral_centroid_hz=2_000,
            onset_strength=0.1,
        ),),
    )
    scores = (
        SemanticLabelScore(label="钢琴", category="乐器线索", similarity=0.5),
        SemanticLabelScore(label="明亮", category="情绪", similarity=0.4),
        SemanticLabelScore(label="贝斯", category="乐器线索", similarity=0.3),
    )
    semantic = MusicSemanticAnalysisResult(
        audio_artifact_id=artifact_id,
        source_name=f"{artifact_id}.wav",
        model_id="test/clap",
        device="test",
        aggregate_label_scores=scores,
        time_segments=(SemanticTimeSegment(
            start_seconds=0,
            end_seconds=0.2,
            label_scores=scores,
        ),),
    )
    return acoustic, semantic


def _valid_llm_payload(*, instrument="钢琴", intent_alignment=None):
    return json.dumps({
        "professional_introduction": (
            "作品以清晰的旋律线条建立明亮而温暖的整体气质，节奏脉动保持克制，"
            "音色层次集中而不过分拥挤。短小的篇幅中，声音由稳定的前景逐渐展开，"
            "形成自然的动态呼吸，并以较为通透的质感完成收束。"
        ),
        "mood_and_character": "整体呈现温暖、明亮而克制的情绪性格，旋律感比强烈节奏感更突出。",
        "instrumentation": [{
            "instrument": instrument,
            "evidence_status": "audio_tendency",
            "description": "音频模型给出了相对明显的钢琴音色线索，但不作为确定的声部分离结论。",
        }],
        "listening_guide": [{
            "section": "开头",
            "start_seconds": 0,
            "end_seconds": 0.2,
            "description": "短段落保持稳定能量，旋律轮廓和明亮音色较为集中。",
        }],
        "intent_alignment": intent_alignment or [],
        "caveats": ["乐器描述来自音色相似度，只表示听感倾向。"],
    }, ensure_ascii=False)


def test_interpretation_uses_real_audio_store_and_preserves_source(tmp_path):
    store, artifact, original = _artifact(tmp_path)
    acoustic, semantic = _analysis_results(artifact.id)

    result = interpret_audio_artifact(
        store.data_root,
        artifact.id,
        acoustic_result=acoustic,
        semantic_result=semantic,
        llm_call=lambda _: _valid_llm_payload(),
    )

    assert result.audio_artifact_id == artifact.id
    assert result.creation_context_quality == "generation_spec_only"
    assert result.narrative.instrumentation[0].instrument == "钢琴"
    assert store.load_audio(artifact.id) == original


def test_invalid_instrument_is_rejected_then_retried(tmp_path):
    store, artifact, _ = _artifact(tmp_path)
    acoustic, semantic = _analysis_results(artifact.id)
    responses = iter([_valid_llm_payload(instrument="小提琴"), _valid_llm_payload()])
    calls = []

    result = interpret_audio_artifact(
        store.data_root,
        artifact.id,
        acoustic_result=acoustic,
        semantic_result=semantic,
        llm_call=lambda prompt: calls.append(prompt) or next(responses),
    )

    assert result.narrative.instrumentation[0].instrument == "钢琴"
    assert len(calls) == 2
    assert "上一次输出未通过校验" in calls[1]


def test_analysis_result_must_belong_to_target_artifact(tmp_path):
    store, artifact, _ = _artifact(tmp_path)
    acoustic, semantic = _analysis_results(uuid4())
    with pytest.raises(ValueError, match="不一致"):
        interpret_audio_artifact(
            store.data_root,
            artifact.id,
            acoustic_result=acoustic,
            semantic_result=semantic,
            llm_call=lambda _: _valid_llm_payload(),
        )


def test_exact_revision_is_resolved_for_matching_audio(tmp_path):
    revision_id = uuid4()
    store, artifact, _ = _artifact(tmp_path, revision_id=revision_id)
    revision = BlueprintRevision(
        id=revision_id,
        draft_id=artifact.draft_id,
        version=2,
        edit_instruction="整体更轻快",
        blueprint=_blueprint(),
    )
    DemoCreationStore(store.data_root).save(DemoCreationRecord(
        creation_id=uuid4(),
        text="完成比赛后很开心",
        garden_id=uuid4(),
        flower_artifact_id=None,
        planting_record_id=None,
        current_audio_artifact_id=artifact.id,
        music_blueprint=_blueprint(),
        music_revision=2,
        music_versions=(DemoMusicVersion(
            revision_id=revision_id,
            audio_artifact_id=artifact.id,
            version=2,
            modification_text="整体更轻快",
            created_at=artifact.created_at,
        ),),
        blueprint_revisions=(revision,),
    ))

    context = resolve_creation_context(store.data_root, artifact.id)

    assert context.quality == "exact_revision"
    assert context.version == 2
    assert context.edit_instruction == "整体更轻快"


def test_blueprint_instruments_and_listening_sections_are_completed(tmp_path):
    revision_id = uuid4()
    store, artifact, _ = _artifact(tmp_path, revision_id=revision_id)
    revision = BlueprintRevision(
        id=revision_id,
        draft_id=artifact.draft_id,
        version=2,
        edit_instruction="整体更轻快",
        blueprint=_blueprint(),
    )
    DemoCreationStore(store.data_root).save(DemoCreationRecord(
        creation_id=uuid4(),
        text="完成比赛后很开心",
        garden_id=uuid4(),
        flower_artifact_id=None,
        planting_record_id=None,
        current_audio_artifact_id=artifact.id,
        music_blueprint=_blueprint(),
        music_revision=2,
        music_versions=(DemoMusicVersion(
            revision_id=revision_id,
            audio_artifact_id=artifact.id,
            version=2,
            modification_text="整体更轻快",
            created_at=artifact.created_at,
        ),),
        blueprint_revisions=(revision,),
    ))
    acoustic, semantic = _analysis_results(artifact.id)

    result = interpret_audio_artifact(
        store.data_root,
        artifact.id,
        acoustic_result=acoustic,
        semantic_result=semantic,
        llm_call=lambda _: _valid_llm_payload(),
    )

    instruments = {item.instrument: item for item in result.narrative.instrumentation}
    assert set(instruments) == {"钢琴", "弦乐", "贝斯"}
    assert instruments["弦乐"].evidence_status == "blueprint_only"
    assert [item.section for item in result.narrative.listening_guide] == ["开头"]


def test_malformed_llm_draft_uses_valid_guarded_fallback(tmp_path):
    revision_id = uuid4()
    store, artifact, _ = _artifact(tmp_path, revision_id=revision_id)
    revision = BlueprintRevision(
        id=revision_id,
        draft_id=artifact.draft_id,
        version=2,
        blueprint=_blueprint(),
    )
    DemoCreationStore(store.data_root).save(DemoCreationRecord(
        creation_id=uuid4(), text="完成比赛后很开心", garden_id=uuid4(),
        flower_artifact_id=None, planting_record_id=None,
        current_audio_artifact_id=artifact.id, music_blueprint=_blueprint(), music_revision=2,
        music_versions=(DemoMusicVersion(
            revision_id=revision_id, audio_artifact_id=artifact.id, version=2,
            modification_text=None, created_at=artifact.created_at,
        ),),
        blueprint_revisions=(revision,),
    ))
    acoustic, semantic = _analysis_results(artifact.id)

    result = interpret_audio_artifact(
        store.data_root, artifact.id, acoustic_result=acoustic, semantic_result=semantic,
        llm_call=lambda _: '{"professional_introduction": "太短"}',
    )

    assert len(result.narrative.professional_introduction) >= 80
    assert {item.instrument for item in result.narrative.instrumentation} == {"钢琴", "弦乐", "贝斯"}


def test_intent_alignment_is_removed_without_edit_instruction(tmp_path):
    store, artifact, _ = _artifact(tmp_path)
    acoustic, semantic = _analysis_results(artifact.id)
    invalid = _valid_llm_payload(intent_alignment=[{
        "intent": "更轻快",
        "assessment": "supported",
        "explanation": "明亮标签较高。",
    }])
    result = interpret_audio_artifact(
        store.data_root,
        artifact.id,
        acoustic_result=acoustic,
        semantic_result=semantic,
        llm_call=lambda _: invalid,
    )

    assert result.narrative.intent_alignment == ()

import math
import struct
import wave
from pathlib import Path
from uuid import uuid4

import pytest

from music_companion.semantic_analysis import (
    CLAP_TRUNCATION_MODE,
    DEFAULT_LABELS,
    SemanticLabel,
    _select_clips,
    analyze_audio_artifact_semantics,
)
from music_engine.audio_store import AudioStore
from music_engine.schema import AceStepGenerationResult, MusicGenerationSpec


class FakeSemanticScorer:
    """不下载模型权重，只验证 Step 2 的 AudioStore、排序和结果契约。"""

    model_id = "test/music-clap"
    device = "test-device"

    def score(self, clips, labels):
        return [[index / 100 for index in range(len(labels))] for _ in clips]


def _wav_bytes(path: Path, seconds: float = 0.25) -> bytes:
    sample_rate = 8_000
    frames = bytearray()
    for index in range(int(sample_rate * seconds)):
        value = int(7_000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        frames.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(frames)
    return path.read_bytes()


def _save_audio_artifact(tmp_path: Path):
    source = tmp_path / "source.wav"
    audio_bytes = _wav_bytes(source)
    store = AudioStore(tmp_path / "audio-store")
    artifact = store.save(
        draft_id=uuid4(),
        revision_id=uuid4(),
        generation_spec=MusicGenerationSpec(
            caption="bright instrumental piano", bpm=100, key="C Major"
        ),
        generation_result=AceStepGenerationResult(
            task_id="semantic-analysis-test",
            audio_bytes=audio_bytes,
            content_type="audio/wav",
        ),
    )
    return store, artifact, audio_bytes


def test_semantic_analysis_reads_real_audio_store_and_ranks_scores(tmp_path):
    store, artifact, original_bytes = _save_audio_artifact(tmp_path)

    result = analyze_audio_artifact_semantics(
        store,
        artifact.id,
        scorer=FakeSemanticScorer(),
        labels=DEFAULT_LABELS[:3],
    )

    assert result.audio_artifact_id == artifact.id
    assert result.source_name == Path(artifact.file_path).name
    assert result.model_id == "test/music-clap"
    assert result.device == "test-device"
    assert result.aggregate_label_scores[0].label == DEFAULT_LABELS[2].label
    assert len(result.time_segments) == 1
    assert store.load_audio(artifact.id) == original_bytes


def test_missing_audio_artifact_has_clear_error(tmp_path):
    with pytest.raises(ValueError, match="音频资产不存在"):
        analyze_audio_artifact_semantics(
            AudioStore(tmp_path / "empty-store"), uuid4(), scorer=FakeSemanticScorer()
        )


def test_clip_selection_is_deterministic_and_covers_beginning_middle_end():
    import numpy

    clips, windows = _select_clips(numpy.zeros(20 * 48_000), 48_000)

    assert len(clips) == 3
    assert windows == [(0, 480_000), (240_000, 720_000), (480_000, 960_000)]


def test_unfused_checkpoint_uses_single_channel_preprocessing_mode():
    assert CLAP_TRUNCATION_MODE == "rand_trunc"


def test_model_result_dimension_mismatch_is_rejected(tmp_path):
    class BrokenScorer(FakeSemanticScorer):
        def score(self, clips, labels):
            return [[0.1]]

    store, artifact, _ = _save_audio_artifact(tmp_path)
    with pytest.raises(RuntimeError, match="评分维度"):
        analyze_audio_artifact_semantics(
            store, artifact.id, scorer=BrokenScorer(), labels=(SemanticLabel("明亮", "情绪", "bright music"), SemanticLabel("平静", "情绪", "calm music"))
        )

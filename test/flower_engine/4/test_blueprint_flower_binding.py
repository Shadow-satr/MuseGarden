"""Step 11：Blueprint 是花朵视觉的唯一生成输入。"""

from pathlib import Path
from uuid import uuid4

from ai_engine.blueprint.schema import MusicBlueprint
from flower_engine import (
    FlowerArtifactStore,
    FlowerLifecycleService,
    blueprint_to_flower_spec,
    build_flower_artifact_from_blueprint,
)
from music_engine import (
    AceStepGenerationResult,
    AudioStore,
    FinalCreation,
    FinalCreationStore,
    MusicGenerationSpec,
    MusicVersionService,
)


def blueprint(**changes: object) -> MusicBlueprint:
    values = {
        "primary_emotion": "满足感",
        "secondary_emotions": ["疲惫", "喜悦"],
        "energy": 0.7,
        "valence": 0.8,
        "tempo": 108,
        "key": "C Major",
        "instruments": ["piano", "strings"],
        "texture": "温暖",
        "scene": "比赛结束之后",
        "progression": "calm_to_rising",
    }
    values.update(changes)
    return MusicBlueprint.model_validate(values)


def visual_snapshot(artifact) -> tuple[dict, dict]:
    return (
        artifact.flower_spec.model_dump(mode="json"),
        artifact.render_spec.model_dump(mode="json"),
    )


def test_complete_blueprint_mapping_is_stable_and_bounded() -> None:
    source = blueprint()
    before = source.model_dump(mode="json")

    first = blueprint_to_flower_spec(source)
    second = blueprint_to_flower_spec(MusicBlueprint.model_validate(before))

    assert first == second
    assert source.model_dump(mode="json") == before
    assert first.species == "tulip"  # texture 优先决定花型
    assert first.palette == "warm_gold"  # primary_emotion 决定色系
    assert first.size == 0.79  # energy 决定花冠尺寸
    assert first.glow == 0.60  # valence + secondary_emotions 决定光感
    assert first.sway_speed == 0.51  # Blueprint tempo 决定初始动画
    assert first.growth_direction == "rising"  # progression 决定生长感


def test_secondary_emotions_and_scene_have_small_deterministic_effects() -> None:
    neutral = blueprint(secondary_emotions=[], scene="比赛结束之后")
    joyful = blueprint(secondary_emotions=["喜悦"], scene="比赛结束之后")
    night = blueprint(secondary_emotions=["喜悦"], scene="深夜")

    neutral_spec = blueprint_to_flower_spec(neutral)
    joyful_spec = blueprint_to_flower_spec(joyful)
    night_spec = blueprint_to_flower_spec(night)

    assert neutral_spec.glow == 0.56
    assert joyful_spec.glow == 0.60
    assert night_spec.glow == 0.52
    assert {spec.species for spec in (neutral_spec, joyful_spec, night_spec)} == {"tulip"}
    assert {spec.palette for spec in (neutral_spec, joyful_spec, night_spec)} == {"warm_gold"}


def test_secondary_emotion_fills_unknown_primary_fallback() -> None:
    source = blueprint(
        primary_emotion="独特心情",
        secondary_emotions=["喜悦"],
        texture="unmapped",
    )
    spec = blueprint_to_flower_spec(source)
    assert spec.species == "sunflower"
    assert spec.palette == "sunlit_yellow"


def test_blueprint_changes_visual_attributes_without_audio_input() -> None:
    source = blueprint()
    changed = blueprint(primary_emotion="悲伤", texture="梦幻", energy=0.2)

    first = build_flower_artifact_from_blueprint(source, 73)
    repeated = build_flower_artifact_from_blueprint(source, 73)
    different = build_flower_artifact_from_blueprint(changed, 73)

    assert visual_snapshot(first) == visual_snapshot(repeated)
    assert first.id != repeated.id  # 生成事件身份独立，视觉内容稳定
    assert visual_snapshot(first) != visual_snapshot(different)
    assert first.flower_spec == blueprint_to_flower_spec(source)


def test_music_versions_do_not_change_persisted_flower(tmp_path: Path) -> None:
    draft_id = uuid4()
    revision_id = uuid4()
    source_blueprint = blueprint()
    audio_store = AudioStore(tmp_path)
    first_audio = audio_store.save(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=MusicGenerationSpec(caption="gentle", bpm=108, key="C Major"),
        generation_result=AceStepGenerationResult(
            task_id="audio-v1", audio_bytes=b"RIFF-v1", content_type="audio/wav"
        ),
    )
    final_store = FinalCreationStore(tmp_path)
    final = FinalCreation(
        draft_id=draft_id,
        revision_id=revision_id,
        memory_id=uuid4(),
        audio_artifact_id=first_audio.id,
        blueprint=source_blueprint,
        audio_artifact=first_audio,
    )
    final_store.save(final)
    flower_store = FlowerArtifactStore(tmp_path)
    flowers = FlowerLifecycleService(final_store, flower_store)
    flower = flowers.create_for_creation(final.id, 73)
    snapshot = flower.model_dump(mode="json")

    second_audio = audio_store.save(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=MusicGenerationSpec(caption="more energetic", bpm=132, key="C Major"),
        generation_result=AceStepGenerationResult(
            task_id="audio-v2", audio_bytes=b"RIFF-v2", content_type="audio/wav"
        ),
    )
    versions = MusicVersionService(audio_store)
    versions.select_current(revision_id, second_audio.id)
    source_blueprint.energy = 0.1  # 外部可变对象不影响冻结的 FinalCreation
    source_blueprint.tempo = 132

    assert versions.get_current_for_revision(revision_id) == second_audio
    assert flower_store.get(flower.id).model_dump(mode="json") == snapshot
    assert flowers.get_current_for_creation(final.id) == flower
    assert visual_snapshot(flowers.create_for_creation(final.id, 73)) == visual_snapshot(flower)


def test_binding_has_no_audio_or_external_generation_dependency() -> None:
    root = Path(__file__).resolve().parents[3]
    source = (root / "flower_engine" / "binding.py").read_text(encoding="utf-8").lower()
    for forbidden in ("audioartifact", "audiostore", "wav", "openai", "requests", "pixi"):
        assert forbidden not in source

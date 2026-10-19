"""Flower Engine Step 7：FinalCreation 关联与花朵历史测试。"""

from pathlib import Path
from uuid import uuid4

import pytest

from ai_engine.blueprint.schema import MusicBlueprint
from flower_engine import (
    FlowerArtifact,
    FlowerArtifactStore,
    FlowerLifecycleService,
    blueprint_to_flower_spec,
    build_flower_render_spec,
    build_flower_variation,
    create_flower_artifact,
)
from music_engine import (
    AudioArtifact,
    FinalCreation,
    FinalCreationStore,
    MusicGenerationSpec,
)


def make_blueprint(*, tempo: int = 108) -> MusicBlueprint:
    return MusicBlueprint(
        primary_emotion="满足感",
        secondary_emotions=["疲劳"],
        energy=0.72,
        valence=0.81,
        tempo=tempo,
        key="C Major",
        instruments=["piano", "strings"],
        texture="warm",
        scene="比赛结束之后",
        progression="calm_to_rising",
    )


def save_final_creation(
    store: FinalCreationStore,
    *,
    blueprint: MusicBlueprint | None = None,
) -> FinalCreation:
    draft_id = uuid4()
    revision_id = uuid4()
    selected_blueprint = blueprint or make_blueprint()
    audio = AudioArtifact(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=MusicGenerationSpec(
            caption="Warm satisfying instrumental.",
            bpm=selected_blueprint.tempo,
            key=selected_blueprint.key,
        ),
        provider_task_id=f"ace-{uuid4()}",
        content_type="audio/wav",
        file_path=f"audio/{uuid4()}.wav",
    )
    final = FinalCreation(
        draft_id=draft_id,
        revision_id=revision_id,
        memory_id=uuid4(),
        audio_artifact_id=audio.id,
        blueprint=selected_blueprint,
        audio_artifact=audio,
    )
    store.save(final)
    return final


def make_service(
    tmp_path: Path,
) -> tuple[FlowerLifecycleService, FinalCreationStore, FlowerArtifactStore]:
    final_store = FinalCreationStore(tmp_path)
    flower_store = FlowerArtifactStore(tmp_path)
    return (
        FlowerLifecycleService(final_store, flower_store),
        final_store,
        flower_store,
    )


def stable_flower_content(artifact: FlowerArtifact) -> dict[str, object]:
    return {
        "creation_id": artifact.creation_id,
        "species": artifact.species,
        "variation_seed": artifact.variation_seed,
        "flower_spec": artifact.flower_spec.model_dump(),
        "render_spec": artifact.render_spec.model_dump(),
        "renderer_schema_version": artifact.renderer_schema_version,
        "template_id": artifact.template_id,
    }


def test_create_for_final_creation_builds_and_persists_linked_flower(
    tmp_path: Path,
) -> None:
    service, final_store, flower_store = make_service(tmp_path)
    final = save_final_creation(final_store)
    original_final = final.model_dump(mode="json")

    artifact = service.create_for_creation(final.id, 12345)

    assert artifact.creation_id == final.id
    assert artifact.species == "tulip"
    assert artifact.variation_seed == 12345
    assert artifact.flower_spec == blueprint_to_flower_spec(final.blueprint)
    assert artifact.template_id == "tulip_v1"
    assert flower_store.get(artifact.id) == artifact
    assert service.list_for_creation(str(final.id)) == [artifact]
    assert service.get_current_for_creation(final.id) == artifact
    assert final.model_dump(mode="json") == original_final

    final.blueprint.tempo = 40
    assert artifact.flower_spec.sway_speed != blueprint_to_flower_spec(final.blueprint).sway_speed


def test_creation_must_exist_before_flower_is_saved(tmp_path: Path) -> None:
    service, _, flower_store = make_service(tmp_path)

    with pytest.raises(ValueError, match="FinalCreation 不存在"):
        service.create_for_creation(uuid4(), 1)
    with pytest.raises(ValueError, match="FinalCreation 不存在"):
        service.list_for_creation(uuid4())
    assert flower_store.list_all() == []


def test_creation_queries_are_isolated_and_empty_is_valid(tmp_path: Path) -> None:
    service, final_store, flower_store = make_service(tmp_path)
    first_creation = save_final_creation(final_store)
    second_creation = save_final_creation(final_store, blueprint=make_blueprint(tempo=80))

    assert service.get_current_for_creation(first_creation.id) is None
    first_flower = service.create_for_creation(first_creation.id, 10)
    second_flower = service.create_for_creation(second_creation.id, 20)

    assert service.list_for_creation(first_creation.id) == [first_flower]
    assert service.list_for_creation(second_creation.id) == [second_flower]
    assert flower_store.list_by_creation(first_creation.id) == [first_flower]
    assert flower_store.get_latest_by_creation(second_creation.id) == second_flower


def test_regenerate_same_seed_preserves_individual_and_history(tmp_path: Path) -> None:
    service, final_store, flower_store = make_service(tmp_path)
    final = save_final_creation(final_store)
    source = service.create_for_creation(final.id, 77)
    source_snapshot = source.model_dump(mode="json")

    regenerated = service.regenerate(source.id)

    assert regenerated.id != source.id
    assert regenerated.creation_id == source.creation_id
    assert stable_flower_content(regenerated) == stable_flower_content(source)
    assert flower_store.get(source.id).model_dump(mode="json") == source_snapshot  # type: ignore[union-attr]
    assert service.list_for_creation(final.id) == [source, regenerated]
    assert service.get_current_for_creation(final.id) == regenerated


def test_regenerate_new_seed_creates_new_individual_without_overwriting(
    tmp_path: Path,
) -> None:
    service, final_store, flower_store = make_service(tmp_path)
    final = save_final_creation(final_store)
    source = service.create_for_creation(final.id, 77)

    regenerated = service.regenerate(source.id, variation_seed=88)

    assert regenerated.variation_seed == 88
    assert regenerated.render_spec != source.render_spec
    assert regenerated.flower_spec == source.flower_spec
    assert flower_store.get(source.id) == source
    assert service.list_for_creation(final.id) == [source, regenerated]


def test_regenerate_rejects_missing_unlinked_or_dangling_artifacts(
    tmp_path: Path,
) -> None:
    service, _, flower_store = make_service(tmp_path)
    with pytest.raises(ValueError, match="FlowerArtifact 不存在"):
        service.regenerate(uuid4())

    spec = blueprint_to_flower_spec(make_blueprint())
    variation = build_flower_variation(spec, 5)
    render = build_flower_render_spec(spec, variation)
    unlinked = create_flower_artifact(spec, render)
    flower_store.save(unlinked)
    with pytest.raises(ValueError, match="尚未关联"):
        service.regenerate(unlinked.id)

    dangling = create_flower_artifact(spec, render, creation_id=uuid4())
    flower_store.save(dangling)
    with pytest.raises(RuntimeError, match="不存在的 FinalCreation"):
        service.regenerate(dangling.id)


@pytest.mark.parametrize("invalid_seed", [-1, True, 1.5, 1 << 63])
def test_invalid_seed_never_creates_partial_history(
    tmp_path: Path,
    invalid_seed: object,
) -> None:
    service, final_store, flower_store = make_service(tmp_path)
    final = save_final_creation(final_store)

    with pytest.raises((TypeError, ValueError)):
        service.create_for_creation(final.id, invalid_seed)  # type: ignore[arg-type]
    assert flower_store.list_all() == []


def test_lifecycle_has_no_llm_network_frontend_or_media_dependency() -> None:
    root = Path(__file__).resolve().parents[3]
    source = (root / "flower_engine" / "lifecycle.py").read_text(
        encoding="utf-8"
    ).lower()
    for forbidden in (
        "openai",
        "ollama",
        "requests",
        "http://",
        "https://",
        "pixi",
        "canvas",
        "sprite",
        "react",
        "image",
        "planting",
        "position",
    ):
        assert forbidden not in source


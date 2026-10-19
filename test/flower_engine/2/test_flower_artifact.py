"""Flower Engine Step 6：FlowerArtifact 与本地生命周期测试。"""

from datetime import timedelta
import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from flower_engine import (
    FlowerArtifact,
    FlowerArtifactStore,
    FlowerRenderSpec,
    FlowerSpec,
    build_flower_render_spec,
    build_flower_variation,
    create_flower_artifact,
)


def make_spec(**changes: object) -> FlowerSpec:
    values: dict[str, object] = {
        "species": "tulip",
        "palette": "warm_gold",
        "size": 0.72,
        "petal_count": 6,
        "stem_height": 0.68,
        "sway_speed": 0.54,
        "glow": 0.31,
        "particle_effect": "sparkles",
        "decoration": "dew_drops",
        "growth_direction": "opening",
    }
    values.update(changes)
    return FlowerSpec.model_validate(values)


def make_artifact(
    *,
    seed: int = 20261012,
    creation_id: UUID | None = None,
) -> tuple[FlowerSpec, FlowerRenderSpec, FlowerArtifact]:
    spec = make_spec()
    variation = build_flower_variation(spec, seed)
    render_spec = build_flower_render_spec(spec, variation)
    artifact = create_flower_artifact(spec, render_spec, creation_id)
    return spec, render_spec, artifact


def visual_snapshot(artifact: FlowerArtifact) -> dict[str, object]:
    """排除生成事件 metadata 后，可重建花朵的稳定内容。"""
    return {
        "creation_id": artifact.creation_id,
        "species": artifact.species,
        "variation_seed": artifact.variation_seed,
        "flower_spec": artifact.flower_spec.model_dump(),
        "render_spec": artifact.render_spec.model_dump(),
        "renderer_schema_version": artifact.renderer_schema_version,
        "template_id": artifact.template_id,
    }


def test_create_artifact_has_complete_serializable_snapshot() -> None:
    creation_id = uuid4()
    spec, render_spec, artifact = make_artifact(creation_id=creation_id)

    assert isinstance(artifact.id, UUID)
    assert artifact.creation_id == creation_id
    assert artifact.species == spec.species == render_spec.species
    assert artifact.variation_seed == render_spec.variation_seed
    assert artifact.renderer_schema_version == "1.0"
    assert artifact.template_id == "tulip_v1"
    assert artifact.created_at.utcoffset() == timedelta(hours=8)
    assert artifact.flower_spec == spec
    assert artifact.render_spec == render_spec
    assert artifact.flower_spec is not spec
    assert artifact.render_spec is not render_spec

    payload = artifact.model_dump(mode="json")
    assert json.loads(artifact.model_dump_json()) == payload
    assert payload["id"] == str(artifact.id)
    assert payload["creation_id"] == str(creation_id)
    assert not ({"image", "file_path", "canvas", "sprite"} & payload.keys())


def test_artifact_is_independent_snapshot_and_does_not_modify_inputs() -> None:
    spec = make_spec()
    variation = build_flower_variation(spec, 17)
    render_spec = build_flower_render_spec(spec, variation)
    original_spec = spec.model_dump()
    original_render = render_spec.model_dump()

    artifact = create_flower_artifact(spec, render_spec)
    assert spec.model_dump() == original_spec
    assert render_spec.model_dump() == original_render

    spec.palette = "cool_blue"
    render_spec.geometry.stem_curve = 1.0
    assert artifact.flower_spec.palette == "warm_gold"
    assert artifact.render_spec.geometry.stem_curve == original_render["geometry"]["stem_curve"]


def test_same_inputs_keep_visual_content_but_each_generation_has_identity() -> None:
    creation_id = uuid4()
    _, _, first = make_artifact(seed=91, creation_id=creation_id)
    _, _, second = make_artifact(seed=91, creation_id=creation_id)

    assert visual_snapshot(first) == visual_snapshot(second)
    assert first.id != second.id

    _, _, other_seed = make_artifact(seed=92, creation_id=creation_id)
    assert other_seed.id not in {first.id, second.id}
    assert visual_snapshot(other_seed) != visual_snapshot(first)
    assert other_seed.variation_seed != first.variation_seed


def test_factory_and_schema_reject_inconsistent_inputs() -> None:
    spec, render_spec, _ = make_artifact()

    with pytest.raises(TypeError, match="flower_spec"):
        create_flower_artifact({}, render_spec)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="render_spec"):
        create_flower_artifact(spec, {})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="creation_id"):
        create_flower_artifact(spec, render_spec, "not-a-uuid")  # type: ignore[arg-type]

    invalid = {
        **create_flower_artifact(spec, render_spec).model_dump(),
        "species": "rose",
    }
    with pytest.raises(ValidationError, match="species"):
        FlowerArtifact.model_validate(invalid)


def test_store_round_trip_list_and_duplicate_protection(tmp_path: Path) -> None:
    store = FlowerArtifactStore(tmp_path)
    assert store.list_all() == []

    _, _, first = make_artifact(seed=1)
    _, _, second = make_artifact(seed=2)
    store.save(first)
    store.save(second)

    assert store.get(first.id) == first
    assert store.get(str(second.id)) == second
    assert store.get(uuid4()) is None
    assert store.list_all() == [first, second]
    assert json.loads(store.file_path.read_text(encoding="utf-8")) == [
        first.model_dump(mode="json"),
        second.model_dump(mode="json"),
    ]

    loaded = store.get(first.id)
    assert loaded is not None
    loaded.flower_spec.palette = "cool_blue"
    assert store.get(first.id).flower_spec.palette == "warm_gold"  # type: ignore[union-attr]

    with pytest.raises(ValueError, match="已存在"):
        store.save(first)
    with pytest.raises(TypeError, match="FlowerArtifact"):
        store.save(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="UUID"):
        store.get("invalid")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{broken", "JSON 格式错误"),
        (json.dumps({"id": "wrong"}), "JSON 列表"),
        (json.dumps([{"id": "wrong"}]), "无效数据"),
    ],
)
def test_store_rejects_corrupt_data(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    store = FlowerArtifactStore(tmp_path)
    store.file_path.parent.mkdir(parents=True, exist_ok=True)
    store.file_path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        store.list_all()


def test_step_6_remains_renderer_and_service_independent() -> None:
    root = Path(__file__).resolve().parents[3]
    sources = "\n".join(
        (root / "flower_engine" / name).read_text(encoding="utf-8").lower()
        for name in ("artifact.py", "store.py")
    )

    for forbidden in (
        "pixi",
        "canvas",
        "sprite",
        "react",
        "openai",
        "ollama",
        "requests",
        "http://",
        "https://",
        "from music_engine",
    ):
        assert forbidden not in sources


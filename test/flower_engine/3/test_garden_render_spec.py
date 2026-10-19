"""Flower Engine Step 9：GardenRenderSpec 与 Domain Adapter 测试。"""

from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from flower_engine import (
    FlowerArtifact,
    FlowerSpec,
    Garden,
    GardenRenderSpec,
    PlantingRecord,
    build_flower_render_spec,
    build_flower_variation,
    create_flower_artifact,
    garden_to_render_spec,
)


def make_artifact(
    species: str,
    *,
    seed: int,
    size: float,
) -> FlowerArtifact:
    species_settings = {
        "tulip": ("warm_gold", 6, "dew_drops"),
        "rose": ("deep_crimson", 10, "light_ribbons"),
        "sunflower": ("sunlit_yellow", 12, "star_charms"),
    }
    palette, petal_count, decoration = species_settings[species]
    spec = FlowerSpec(
        species=species,
        palette=palette,
        size=size,
        petal_count=petal_count,
        stem_height=0.68,
        sway_speed=0.54,
        glow=0.31,
        particle_effect="sparkles",
        decoration=decoration,
        growth_direction="opening",
    )
    variation = build_flower_variation(spec, seed)
    render = build_flower_render_spec(spec, variation)
    return create_flower_artifact(spec, render)


def test_garden_domain_converts_to_complete_render_spec() -> None:
    garden = Garden(name="Preview", width=10, height=6)
    flower = make_artifact("tulip", seed=1, size=0.4)
    planting = PlantingRecord(
        garden_id=garden.id,
        flower_artifact_id=flower.id,
        x=2,
        y=1,
    )

    render = garden_to_render_spec(garden, [planting], [flower])

    assert isinstance(render, GardenRenderSpec)
    assert render.renderer_schema_version == "1.0"
    assert render.garden_id == garden.id
    assert (render.grid_width, render.grid_height) == (10, 6)
    assert render.cell_size == 48
    assert (render.pixel_width, render.pixel_height) == (480, 288)
    assert render.background.style == "meadow"
    assert render.model_dump_json()

    item = render.flowers[0]
    assert item.planting_record_id == planting.id
    assert item.flower_artifact_id == flower.id
    assert item.template_id == "tulip_v1"
    assert (item.grid_x, item.grid_y) == (2, 1)
    assert (item.pixel_x, item.pixel_y) == (120.0, 96.0)
    assert item.scale == 0.95
    assert item.z_index == 12
    assert item.render_spec == flower.render_spec


def test_assets_scale_and_depth_are_deterministic_and_sorted() -> None:
    garden = Garden(name="Layering", width=12, height=8)
    rose = make_artifact("rose", seed=2, size=1.0)
    tulip = make_artifact("tulip", seed=3, size=0.0)
    sunflower = make_artifact("sunflower", seed=4, size=0.7)
    plantings = [
        PlantingRecord(garden_id=garden.id, flower_artifact_id=rose.id, x=8, y=6),
        PlantingRecord(garden_id=garden.id, flower_artifact_id=tulip.id, x=1, y=1),
        PlantingRecord(garden_id=garden.id, flower_artifact_id=sunflower.id, x=4, y=4),
    ]

    render = garden_to_render_spec(
        garden,
        list(reversed(plantings)),
        [sunflower, rose, tulip],
    )

    assert [flower.template_id for flower in render.flowers] == [
        "tulip_v1",
        "sunflower_v1",
        "rose_v1",
    ]
    assert [flower.scale for flower in render.flowers] == [0.75, 1.1, 1.25]
    assert [flower.z_index for flower in render.flowers] == [13, 52, 80]


def test_adapter_does_not_modify_domain_or_artifact_objects() -> None:
    garden = Garden(name="Immutable Inputs", width=7, height=5)
    flower = make_artifact("rose", seed=9, size=0.6)
    planting = PlantingRecord(
        garden_id=garden.id,
        flower_artifact_id=flower.id,
        x=5,
        y=3,
    )
    before = (
        garden.model_dump(mode="json"),
        planting.model_dump(mode="json"),
        flower.model_dump(mode="json"),
    )

    first = garden_to_render_spec(garden, [planting], [flower], cell_size=64)
    second = garden_to_render_spec(garden, [planting], [flower], cell_size=64)

    assert first == second
    assert before == (
        garden.model_dump(mode="json"),
        planting.model_dump(mode="json"),
        flower.model_dump(mode="json"),
    )


def test_adapter_rejects_missing_cross_garden_out_of_bounds_and_conflicts() -> None:
    garden = Garden(name="Validation", width=4, height=3)
    flower = make_artifact("tulip", seed=11, size=0.5)
    valid = PlantingRecord(
        garden_id=garden.id,
        flower_artifact_id=flower.id,
        x=1,
        y=1,
    )

    with pytest.raises(ValueError, match="缺失"):
        garden_to_render_spec(garden, [valid], [])

    wrong_garden = valid.model_copy(update={"garden_id": uuid4()})
    with pytest.raises(ValueError, match="不属于"):
        garden_to_render_spec(garden, [wrong_garden], [flower])

    outside = valid.model_copy(update={"x": garden.width})
    with pytest.raises(ValueError, match="超出"):
        garden_to_render_spec(garden, [outside], [flower])

    conflict = valid.model_copy(update={"id": uuid4()})
    with pytest.raises(ValueError, match="重复种植位置"):
        garden_to_render_spec(garden, [valid, conflict], [flower])

    with pytest.raises(ValueError, match="重复 ID"):
        garden_to_render_spec(garden, [valid], [flower, flower])


@pytest.mark.parametrize("cell_size", [True, 1.5, "48"])
def test_adapter_rejects_non_integer_cell_size(cell_size: object) -> None:
    garden = Garden(name="Cell", width=4, height=3)
    with pytest.raises(TypeError, match="cell_size"):
        garden_to_render_spec(garden, [], [], cell_size=cell_size)  # type: ignore[arg-type]


@pytest.mark.parametrize("cell_size", [23, 97])
def test_adapter_rejects_out_of_range_cell_size(cell_size: int) -> None:
    garden = Garden(name="Cell", width=4, height=3)
    with pytest.raises(ValueError, match="24-96"):
        garden_to_render_spec(garden, [], [], cell_size=cell_size)


def test_garden_render_schema_rejects_bad_dimensions_order_and_template() -> None:
    garden = Garden(name="Schema", width=4, height=3)
    flower = make_artifact("tulip", seed=12, size=0.5)
    first = PlantingRecord(
        garden_id=garden.id,
        flower_artifact_id=flower.id,
        x=0,
        y=0,
    )
    second = PlantingRecord(
        garden_id=garden.id,
        flower_artifact_id=flower.id,
        x=1,
        y=1,
    )
    valid = garden_to_render_spec(garden, [first, second], [flower]).model_dump()

    with pytest.raises(ValidationError, match="pixel_width"):
        GardenRenderSpec.model_validate({**valid, "pixel_width": 999})
    with pytest.raises(ValidationError, match="z_index"):
        GardenRenderSpec.model_validate(
            {**valid, "flowers": list(reversed(valid["flowers"]))}
        )

    bad_flower = {**valid["flowers"][0], "template_id": "rose_v1"}
    with pytest.raises(ValidationError, match="template_id"):
        GardenRenderSpec.model_validate(
            {**valid, "flowers": [bad_flower, valid["flowers"][1]]}
        )


def test_adapter_has_no_storage_renderer_llm_or_network_dependency() -> None:
    root = Path(__file__).resolve().parents[3]
    source = (root / "flower_engine" / "garden_adapter.py").read_text(
        encoding="utf-8"
    ).lower()
    for forbidden in (
        "from flower_engine.store",
        "from flower_engine.garden_store",
        "from flower_engine.renderer",
        "openai",
        "ollama",
        "requests",
        "http://",
        "https://",
        "pixi",
        "react",
    ):
        assert forbidden not in source


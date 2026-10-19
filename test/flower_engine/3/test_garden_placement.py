"""Flower Engine Step 8：Garden Placement Domain 测试。"""

from datetime import timedelta
import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from flower_engine import (
    FlowerArtifact,
    FlowerArtifactStore,
    FlowerSpec,
    Garden,
    GardenService,
    GardenStore,
    PlantingRecord,
    build_flower_render_spec,
    build_flower_variation,
    create_flower_artifact,
)


def make_flower(seed: int = 101) -> FlowerArtifact:
    spec = FlowerSpec(
        species="tulip",
        palette="warm_gold",
        size=0.72,
        petal_count=6,
        stem_height=0.68,
        sway_speed=0.54,
        glow=0.31,
        particle_effect="sparkles",
        decoration="dew_drops",
        growth_direction="opening",
    )
    variation = build_flower_variation(spec, seed)
    render = build_flower_render_spec(spec, variation)
    return create_flower_artifact(spec, render)


def make_service(
    tmp_path: Path,
) -> tuple[GardenService, GardenStore, FlowerArtifactStore]:
    garden_store = GardenStore(tmp_path)
    flower_store = FlowerArtifactStore(tmp_path)
    return GardenService(garden_store, flower_store), garden_store, flower_store


def test_garden_model_and_creation_are_complete_and_serializable(
    tmp_path: Path,
) -> None:
    service, store, _ = make_service(tmp_path)
    garden = service.create_garden("  My Garden  ", 20, 15)

    assert isinstance(garden.id, UUID)
    assert garden.name == "My Garden"
    assert garden.width == 20
    assert garden.height == 15
    assert garden.created_at.utcoffset() == timedelta(hours=8)
    assert store.get_garden(garden.id) == garden
    assert json.loads(garden.model_dump_json()) == garden.model_dump(mode="json")
    assert service.get_garden_layout(garden.id) == []


@pytest.mark.parametrize(
    "values",
    [
        {"name": "", "width": 20, "height": 20},
        {"name": "Garden", "width": 0, "height": 20},
        {"name": "Garden", "width": 20, "height": -1},
        {"name": "Garden", "width": True, "height": 20},
        {"name": "Garden", "width": 20.5, "height": 20},
    ],
)
def test_garden_schema_rejects_invalid_dimensions_and_name(
    values: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        Garden.model_validate(values)


def test_flower_can_be_planted_and_layout_is_persisted(tmp_path: Path) -> None:
    service, garden_store, flower_store = make_service(tmp_path)
    garden = service.create_garden("Memory Garden", 12, 8)
    flower = make_flower()
    flower_store.save(flower)

    planting = service.plant_flower(garden.id, flower.id, 5, 7)

    assert isinstance(planting, PlantingRecord)
    assert planting.garden_id == garden.id
    assert planting.flower_artifact_id == flower.id
    assert (planting.x, planting.y) == (5, 7)
    assert planting.planted_at.utcoffset() == timedelta(hours=8)
    assert service.get_garden_layout(str(garden.id)) == [planting]
    assert garden_store.list_plantings(garden.id) == [planting]
    assert json.loads(garden_store.plantings_file.read_text(encoding="utf-8")) == [
        planting.model_dump(mode="json")
    ]


@pytest.mark.parametrize(
    ("x", "y", "error_type"),
    [
        (-1, 0, ValueError),
        (4, 0, ValueError),
        (0, -1, ValueError),
        (0, 3, ValueError),
        (True, 0, TypeError),
        (0, 1.5, TypeError),
    ],
)
def test_invalid_coordinates_fail_without_partial_record(
    tmp_path: Path,
    x: object,
    y: object,
    error_type: type[Exception],
) -> None:
    service, garden_store, flower_store = make_service(tmp_path)
    garden = service.create_garden("Small", 4, 3)
    flower = make_flower()
    flower_store.save(flower)

    with pytest.raises(error_type):
        service.plant_flower(garden.id, flower.id, x, y)  # type: ignore[arg-type]
    assert garden_store.list_plantings(garden.id) == []


def test_position_conflict_is_scoped_to_one_garden(tmp_path: Path) -> None:
    service, garden_store, flower_store = make_service(tmp_path)
    first_garden = service.create_garden("First", 10, 10)
    second_garden = service.create_garden("Second", 10, 10)
    first_flower = make_flower(1)
    second_flower = make_flower(2)
    flower_store.save(first_flower)
    flower_store.save(second_flower)

    first_planting = service.plant_flower(first_garden.id, first_flower.id, 3, 4)
    with pytest.raises(ValueError, match="已经有花"):
        service.plant_flower(first_garden.id, second_flower.id, 3, 4)
    second_planting = service.plant_flower(second_garden.id, second_flower.id, 3, 4)

    assert garden_store.list_plantings(first_garden.id) == [first_planting]
    assert garden_store.list_plantings(second_garden.id) == [second_planting]


def test_same_flower_may_be_displayed_at_multiple_positions(tmp_path: Path) -> None:
    service, _, flower_store = make_service(tmp_path)
    garden = service.create_garden("Copies", 10, 10)
    flower = make_flower()
    flower_store.save(flower)

    first = service.plant_flower(garden.id, flower.id, 1, 1)
    second = service.plant_flower(garden.id, flower.id, 2, 2)

    assert first.flower_artifact_id == second.flower_artifact_id == flower.id
    assert service.get_garden_layout(garden.id) == [first, second]


def test_missing_garden_or_flower_is_rejected(tmp_path: Path) -> None:
    service, garden_store, _ = make_service(tmp_path)
    garden = service.create_garden("Empty", 5, 5)

    with pytest.raises(ValueError, match="Garden 不存在"):
        service.get_garden_layout(uuid4())
    with pytest.raises(ValueError, match="Garden 不存在"):
        service.plant_flower(uuid4(), uuid4(), 0, 0)
    with pytest.raises(ValueError, match="FlowerArtifact 不存在"):
        service.plant_flower(garden.id, uuid4(), 0, 0)
    assert garden_store.list_plantings() == []


def test_planting_history_is_independent_from_flower_changes_or_removal(
    tmp_path: Path,
) -> None:
    service, _, flower_store = make_service(tmp_path)
    garden = service.create_garden("History", 8, 8)
    flower = make_flower()
    flower_store.save(flower)
    planting = service.plant_flower(garden.id, flower.id, 6, 2)
    original_record = planting.model_dump(mode="json")

    flower.flower_spec.palette = "cool_blue"
    assert planting.model_dump(mode="json") == original_record

    flower_store.file_path.write_text("[]", encoding="utf-8")
    assert flower_store.get(flower.id) is None
    assert service.get_garden_layout(garden.id) == [planting]


def test_store_rejects_duplicates_invalid_types_and_corrupt_json(
    tmp_path: Path,
) -> None:
    store = GardenStore(tmp_path)
    garden = Garden(name="Store", width=4, height=4)
    store.save_garden(garden)
    with pytest.raises(ValueError, match="已存在"):
        store.save_garden(garden)
    with pytest.raises(TypeError, match="Garden"):
        store.save_garden(object())  # type: ignore[arg-type]

    planting = PlantingRecord(
        garden_id=garden.id,
        flower_artifact_id=uuid4(),
        x=0,
        y=0,
    )
    store.save_planting(planting)
    with pytest.raises(ValueError, match="已存在"):
        store.save_planting(planting)
    with pytest.raises(TypeError, match="PlantingRecord"):
        store.save_planting(object())  # type: ignore[arg-type]

    store.gardens_file.write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON 格式错误"):
        store.list_gardens()
    store.plantings_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON 列表"):
        store.list_plantings()


def test_garden_domain_has_no_renderer_frontend_llm_or_network_dependency() -> None:
    root = Path(__file__).resolve().parents[3]
    source = "\n".join(
        (root / "flower_engine" / name).read_text(encoding="utf-8").lower()
        for name in ("garden_store.py", "garden_service.py")
    )
    for forbidden in (
        "renderer",
        "pixi",
        "canvas",
        "sprite",
        "react",
        "openai",
        "ollama",
        "requests",
        "http://",
        "https://",
        "drag",
        "season",
        "growth",
    ):
        assert forbidden not in source


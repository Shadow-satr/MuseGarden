"""Frontend Step 14：1×1 / 3×3 花朵占地规则。"""

from uuid import uuid4

import pytest

from application.garden_planting import footprint, plan_planting
from flower_engine.schema import PlantingRecord


def terrain_planting(
    x: int,
    y: int,
    *,
    size: str = "small",
    tiles: tuple[tuple[int, int], ...] | None = None,
) -> PlantingRecord:
    occupied = tiles if tiles is not None else footprint((x, y), size)  # type: ignore[arg-type]
    return PlantingRecord(
        garden_id=uuid4(),
        flower_artifact_id=uuid4(),
        x=x,
        y=y,
        placement_schema_version="terrain-v1",
        flower_size=size,
        occupied_tiles=occupied,
    )


def test_small_flower_occupies_only_selected_center() -> None:
    plan = plan_planting((22, 18), [], prefer_large=False)
    assert plan.flower_size == "small"
    assert plan.occupied_tiles == ((22, 18),)


def test_large_flower_uses_selected_center_and_three_by_three_footprint() -> None:
    plan = plan_planting((22, 18), [], prefer_large=True)
    assert plan.flower_size == "large"
    assert plan.plot_id == "north-west"
    assert plan.occupied_tiles == (
        (21, 17), (22, 17), (23, 17),
        (21, 18), (22, 18), (23, 18),
        (21, 19), (22, 19), (23, 19),
    )


@pytest.mark.parametrize("center", [(62, 18), (65, 19), (66, 19)])
def test_large_flower_downgrades_at_field_edge_gap_or_nonsoil_neighbor(
    center: tuple[int, int],
) -> None:
    if center == (66, 19):
        with pytest.raises(ValueError, match="SOIL"):
            plan_planting(center, [], prefer_large=True)
        return
    plan = plan_planting(center, [], prefer_large=True)
    assert plan.flower_size == "small"
    assert plan.occupied_tiles == (center,)


@pytest.mark.parametrize("center", [(25, 18), (26, 21), (61, 45)])
def test_merged_fields_turn_former_gaps_into_plantable_soil(
    center: tuple[int, int],
) -> None:
    plan = plan_planting(center, [], prefer_large=False)
    assert plan.flower_size == "small"
    assert plan.occupied_tiles == (center,)


def test_large_flower_downgrades_when_neighboring_tile_is_occupied() -> None:
    neighbor = terrain_planting(23, 18)
    plan = plan_planting((22, 18), [neighbor], prefer_large=True)
    assert plan.flower_size == "small"
    assert plan.occupied_tiles == ((22, 18),)


def test_occupied_center_rejects_planting_instead_of_downgrading() -> None:
    existing = terrain_planting(22, 18)
    with pytest.raises(ValueError, match="已经有花"):
        plan_planting((22, 18), [existing], prefer_large=True)


def test_historical_record_without_size_fields_defaults_to_small() -> None:
    historical = PlantingRecord(
        garden_id=uuid4(), flower_artifact_id=uuid4(), x=8, y=5,
    )
    assert historical.placement_schema_version == "legacy"
    assert historical.flower_size == "small"
    assert historical.occupied_tiles == ()

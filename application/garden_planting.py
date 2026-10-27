"""MuseGarden Grid Map V1 的种植占地规则。"""

from dataclasses import dataclass
from typing import Literal, Sequence

from flower_engine.schema import PlantingRecord


FlowerSize = Literal["small", "large"]
Tile = tuple[int, int]

FARM_PLOT_ORIGINS: tuple[tuple[str, int, int], ...] = (
    ("north-west", 21, 17),
    ("north-east", 62, 18),
    ("south-west", 21, 41),
    ("south-east", 57, 41),
)
SLOT_SIZE = 4
SLOT_GAP = 1
MERGED_FARM_PLOT_IDS = frozenset({"north-west", "south-east"})


@dataclass(frozen=True)
class PlantingPlan:
    center: Tile
    flower_size: FlowerSize
    occupied_tiles: tuple[Tile, ...]
    plot_id: str


def soil_plot_at(tile: Tile) -> str | None:
    """返回地形格所属田地；西北和东南田地内部为连续 SOIL。"""
    x, y = tile
    for plot_id, origin_x, origin_y in FARM_PLOT_ORIGINS:
        local_x = x - origin_x
        local_y = y - origin_y
        if not 0 <= local_x < 14 or not 0 <= local_y < 9:
            continue
        if plot_id in MERGED_FARM_PLOT_IDS:
            return plot_id
        if local_x % (SLOT_SIZE + SLOT_GAP) < SLOT_SIZE and local_y % (SLOT_SIZE + SLOT_GAP) < SLOT_SIZE:
            return plot_id
    return None


def footprint(center: Tile, flower_size: FlowerSize) -> tuple[Tile, ...]:
    x, y = center
    if flower_size == "small":
        return (center,)
    return tuple(
        (tile_x, tile_y)
        for tile_y in range(y - 1, y + 2)
        for tile_x in range(x - 1, x + 2)
    )


def legacy_terrain_tile(x: int, y: int) -> Tile | None:
    """把 Step 13 前的 24 个后端格映射到旧田块中心附近的单个地形格。"""
    plot_column = (x - 7) // 3
    plot_row = (y - 4) // 2
    if plot_column not in (0, 1) or plot_row not in (0, 1):
        return None
    slot_column = (x - 7) % 3
    slot_row = (y - 4) % 2
    if not 0 <= slot_column < 3 or not 0 <= slot_row < 2:
        return None
    plot_index = plot_row * 2 + plot_column
    _, origin_x, origin_y = FARM_PLOT_ORIGINS[plot_index]
    return (
        origin_x + slot_column * (SLOT_SIZE + SLOT_GAP) + 2,
        origin_y + slot_row * (SLOT_SIZE + SLOT_GAP) + 2,
    )


def occupied_tiles_for(planting: PlantingRecord) -> tuple[Tile, ...]:
    if planting.placement_schema_version == "terrain-v1":
        return planting.occupied_tiles
    legacy = legacy_terrain_tile(planting.x, planting.y)
    return (legacy,) if legacy is not None else ()


def plan_planting(
    center: Tile,
    existing: Sequence[PlantingRecord],
    *,
    prefer_large: bool,
) -> PlantingPlan:
    """验证中心格，尝试 3×3 大花，失败时确定性降级为 1×1 小花。"""
    plot_id = soil_plot_at(center)
    if plot_id is None:
        raise ValueError("只能在 SOIL 地形格种花")

    occupied = {
        tile
        for planting in existing
        for tile in occupied_tiles_for(planting)
    }
    if center in occupied:
        raise ValueError(f"花园位置 ({center[0]}, {center[1]}) 已经有花")

    if prefer_large:
        large_tiles = footprint(center, "large")
        if (
            all(soil_plot_at(tile) == plot_id for tile in large_tiles)
            and not occupied.intersection(large_tiles)
        ):
            return PlantingPlan(center, "large", large_tiles, plot_id)

    return PlantingPlan(center, "small", footprint(center, "small"), plot_id)

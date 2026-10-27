"""将 Garden Domain 快照转换为与存储无关的 GardenRenderSpec。"""

from collections.abc import Sequence

from flower_engine.schema import (
    FlowerArtifact,
    Garden,
    GardenRenderFlower,
    GardenRenderSpec,
    PlantingRecord,
)


DEFAULT_GARDEN_CELL_SIZE = 48


def garden_to_render_spec(
    garden: Garden,
    plantings: Sequence[PlantingRecord],
    artifacts: Sequence[FlowerArtifact],
    *,
    cell_size: int = DEFAULT_GARDEN_CELL_SIZE,
) -> GardenRenderSpec:
    """把已加载的领域对象转换成确定性像素场景，不读取 Storage。"""
    if not isinstance(garden, Garden):
        raise TypeError("garden 必须是 Garden 实例")
    if not isinstance(cell_size, int) or isinstance(cell_size, bool):
        raise TypeError("cell_size 必须是整数")
    if not 24 <= cell_size <= 96:
        raise ValueError("cell_size 必须位于 24-96")
    if any(not isinstance(item, PlantingRecord) for item in plantings):
        raise TypeError("plantings 必须只包含 PlantingRecord")
    if any(not isinstance(item, FlowerArtifact) for item in artifacts):
        raise TypeError("artifacts 必须只包含 FlowerArtifact")

    artifacts_by_id = {artifact.id: artifact for artifact in artifacts}
    if len(artifacts_by_id) != len(artifacts):
        raise ValueError("artifacts 不能包含重复 ID")

    occupied: set[tuple[int, int]] = set()
    render_flowers: list[GardenRenderFlower] = []
    for planting in plantings:
        if planting.garden_id != garden.id:
            raise ValueError("PlantingRecord 不属于当前 Garden")
        if planting.x >= garden.width or planting.y >= garden.height:
            raise ValueError("PlantingRecord 坐标超出 Garden 边界")
        planting_tiles = set(planting.occupied_tiles or ((planting.x, planting.y),))
        if occupied.intersection(planting_tiles):
            raise ValueError("Garden 中存在重复种植位置")
        occupied.update(planting_tiles)

        artifact = artifacts_by_id.get(planting.flower_artifact_id)
        if artifact is None:
            raise ValueError(
                f"PlantingRecord 引用了缺失的 FlowerArtifact：{planting.flower_artifact_id}"
            )

        render_flowers.append(
            GardenRenderFlower(
                planting_record_id=planting.id,
                flower_artifact_id=artifact.id,
                template_id=artifact.template_id,
                grid_x=planting.x,
                grid_y=planting.y,
                pixel_x=round((planting.x + 0.5) * cell_size, 4),
                pixel_y=round((planting.y + 1) * cell_size, 4),
                scale=round(0.75 + artifact.flower_spec.size * 0.5, 4),
                z_index=planting.y * garden.width + planting.x,
                placement_schema_version=planting.placement_schema_version,
                flower_size=planting.flower_size,
                occupied_tiles=planting.occupied_tiles,
                render_spec=artifact.render_spec,
            )
        )

    render_flowers.sort(key=lambda flower: flower.z_index)
    return GardenRenderSpec(
        garden_id=garden.id,
        grid_width=garden.width,
        grid_height=garden.height,
        cell_size=cell_size,
        pixel_width=garden.width * cell_size,
        pixel_height=garden.height * cell_size,
        flowers=tuple(render_flowers),
    )

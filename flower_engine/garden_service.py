"""Garden Placement 领域服务：创建空间、种花与查询布局。"""

from uuid import UUID

from flower_engine.garden_store import GardenStore
from flower_engine.schema import Garden, PlantingRecord
from flower_engine.store import FlowerArtifactStore


class GardenService:
    """执行跨 Garden、PlantingRecord 与 FlowerArtifact 的空间规则。"""

    def __init__(
        self,
        garden_store: GardenStore,
        flower_store: FlowerArtifactStore,
    ) -> None:
        if not isinstance(garden_store, GardenStore):
            raise TypeError("garden_store 必须是 GardenStore 实例")
        if not isinstance(flower_store, FlowerArtifactStore):
            raise TypeError("flower_store 必须是 FlowerArtifactStore 实例")
        self.garden_store = garden_store
        self.flower_store = flower_store

    def create_garden(self, name: str, width: int, height: int) -> Garden:
        """创建并持久化一个空的整数网格花园。"""
        garden = Garden(name=name, width=width, height=height)
        self.garden_store.save_garden(garden)
        return garden

    def plant_flower(
        self,
        garden_id: UUID | str,
        flower_artifact_id: UUID | str,
        x: int,
        y: int,
    ) -> PlantingRecord:
        """验证引用、边界和位置冲突后，把花种进指定网格。"""
        garden = self.garden_store.get_garden(garden_id)
        if garden is None:
            raise ValueError(f"Garden 不存在：{garden_id}")
        flower = self.flower_store.get(flower_artifact_id)
        if flower is None:
            raise ValueError(f"FlowerArtifact 不存在：{flower_artifact_id}")
        garden = self.validate_planting_position(garden_id, x, y)

        planting = PlantingRecord(
            garden_id=garden.id,
            flower_artifact_id=flower.id,
            x=x,
            y=y,
        )
        self.garden_store.save_planting(planting)
        return planting

    def validate_planting_position(
        self,
        garden_id: UUID | str,
        x: int,
        y: int,
    ) -> Garden:
        """在耗时生成前预检位置；真正保存时仍重新检查。"""
        garden = self.garden_store.get_garden(garden_id)
        if garden is None:
            raise ValueError(f"Garden 不存在：{garden_id}")
        _validate_coordinate("x", x, garden.width)
        _validate_coordinate("y", y, garden.height)
        if any(
            planting.x == x and planting.y == y
            for planting in self.garden_store.list_plantings(garden.id)
        ):
            raise ValueError(f"花园位置 ({x}, {y}) 已经有花")
        return garden

    def get_garden_layout(
        self,
        garden_id: UUID | str,
    ) -> list[PlantingRecord]:
        """返回指定花园按种植时间排列的稳定空间记录。"""
        garden = self.garden_store.get_garden(garden_id)
        if garden is None:
            raise ValueError(f"Garden 不存在：{garden_id}")
        return self.garden_store.list_plantings(garden.id)

    def dig_up_flower(self, garden_id: UUID | str, planting_record_id: UUID | str) -> PlantingRecord:
        """永久移除一处种植；仅在资产不再被任何花园引用时删除花资产。"""
        garden = self.garden_store.get_garden(garden_id)
        if garden is None:
            raise ValueError(f"Garden 不存在：{garden_id}")
        target = next(
            (item for item in self.garden_store.list_plantings(garden.id)
             if item.id == UUID(str(planting_record_id))),
            None,
        )
        if target is None:
            raise ValueError("此花不在指定花园中")
        removed = self.garden_store.delete_planting(target.id)
        if not any(
            item.flower_artifact_id == target.flower_artifact_id
            for item in self.garden_store.list_plantings()
        ):
            self.flower_store.delete(target.flower_artifact_id)
        return removed


def _validate_coordinate(name: str, value: int, upper_bound: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} 必须是整数")
    if value < 0 or value >= upper_bound:
        raise ValueError(
            f"{name} 必须位于 0 到 {upper_bound - 1} 之间"
        )

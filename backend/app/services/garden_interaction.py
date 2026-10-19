"""Step 10 应用层：调用 Garden Domain 并返回刷新后的渲染快照。"""

from pathlib import Path
from uuid import UUID

from backend.app.schemas.garden import AvailableFlower, GardenPreviewResponse
from flower_engine import (
    FlowerArtifactStore,
    GardenService,
    GardenStore,
    garden_to_render_spec,
)


class GardenInteractionService:
    """连接 HTTP 交互与既有 GardenService，不复制领域校验规则。"""

    def __init__(
        self,
        garden_store: GardenStore,
        flower_store: FlowerArtifactStore,
    ) -> None:
        self.garden_store = garden_store
        self.flower_store = flower_store
        self.garden_service = GardenService(garden_store, flower_store)

    def get_preview(self, garden_id: UUID | str) -> GardenPreviewResponse:
        garden = self.garden_store.get_garden(garden_id)
        if garden is None:
            raise ValueError(f"Garden 不存在：{garden_id}")
        plantings = self.garden_service.get_garden_layout(garden.id)
        artifacts = self.flower_store.list_all()
        return GardenPreviewResponse(
            garden=garden_to_render_spec(garden, plantings, artifacts),
            available_flowers=tuple(
                AvailableFlower(
                    flower_artifact_id=artifact.id,
                    species=artifact.species,
                    template_id=artifact.template_id,
                    scale=round(0.75 + artifact.flower_spec.size * 0.5, 4),
                    render_spec=artifact.render_spec,
                )
                for artifact in artifacts
            ),
        )

    def plant_and_refresh(
        self,
        garden_id: UUID | str,
        flower_artifact_id: UUID | str,
        x: int,
        y: int,
    ) -> GardenPreviewResponse:
        self.garden_service.plant_flower(
            garden_id,
            flower_artifact_id,
            x,
            y,
        )
        return self.get_preview(garden_id)


def build_preview_service(data_root: Path) -> GardenInteractionService:
    return GardenInteractionService(
        GardenStore(data_root),
        FlowerArtifactStore(data_root),
    )

"""Flower Engine Step 10：真实种植交互应用层测试。"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.schemas import PlantFlowerRequest
from backend.app.services import GardenInteractionService
from flower_engine import FlowerArtifactStore, GardenStore
from scripts.export_garden_preview_spec import build_preview_domain


def build_service(data_root: Path):
    garden, artifacts, plantings = build_preview_domain()
    garden_store = GardenStore(data_root)
    flower_store = FlowerArtifactStore(data_root)
    garden_store.save_garden(garden)
    for artifact in artifacts:
        flower_store.save(artifact)
    for planting in plantings:
        garden_store.save_planting(planting)
    return GardenInteractionService(garden_store, flower_store), garden, artifacts


def test_preview_exposes_real_garden_and_available_artifacts(tmp_path: Path) -> None:
    service, garden, artifacts = build_service(tmp_path)

    preview = service.get_preview(garden.id)

    assert preview.garden.garden_id == garden.id
    assert len(preview.garden.flowers) == 9
    assert {item.flower_artifact_id for item in preview.available_flowers} == {
        artifact.id for artifact in artifacts
    }
    assert all(0.75 <= item.scale <= 1.25 for item in preview.available_flowers)


def test_planting_calls_domain_persists_record_and_returns_fresh_render_spec(
    tmp_path: Path,
) -> None:
    service, garden, artifacts = build_service(tmp_path)

    refreshed = service.plant_and_refresh(garden.id, artifacts[0].id, 3, 3)

    matching = [
        item for item in service.garden_store.list_plantings(garden.id)
        if item.x == 3 and item.y == 3
    ]
    assert len(matching) == 1
    assert matching[0].flower_artifact_id == artifacts[0].id
    assert len(refreshed.garden.flowers) == 10
    assert any(item.grid_x == 3 and item.grid_y == 3 for item in refreshed.garden.flowers)


def test_domain_remains_authoritative_for_conflicts_and_bounds(tmp_path: Path) -> None:
    service, garden, artifacts = build_service(tmp_path)
    original_count = len(service.garden_store.list_plantings(garden.id))

    with pytest.raises(ValueError, match="已经有花"):
        service.plant_and_refresh(garden.id, artifacts[0].id, 11, 1)
    with pytest.raises(ValueError, match="0 到 15"):
        service.plant_and_refresh(garden.id, artifacts[0].id, 16, 2)

    assert len(service.garden_store.list_plantings(garden.id)) == original_count


def test_interaction_does_not_mutate_garden_or_flower_artifact(tmp_path: Path) -> None:
    service, garden, artifacts = build_service(tmp_path)
    garden_before = garden.model_dump(mode="json")
    artifact_before = artifacts[0].model_dump(mode="json")

    service.plant_and_refresh(garden.id, artifacts[0].id, 3, 3)

    assert garden.model_dump(mode="json") == garden_before
    assert artifacts[0].model_dump(mode="json") == artifact_before


@pytest.mark.parametrize(
    "field,value",
    [("x", True), ("x", 1.5), ("y", False), ("y", 2.5)],
)
def test_request_contract_rejects_non_integer_coordinates(field: str, value: object) -> None:
    _, _, artifacts = build_preview_domain()
    data = {"flower_artifact_id": artifacts[0].id, "x": 1, "y": 2}
    data[field] = value

    with pytest.raises(ValidationError):
        PlantFlowerRequest.model_validate(data)


def test_interaction_layer_has_no_llm_or_renderer_dependency() -> None:
    source = Path("backend/app/services/garden_interaction.py").read_text(encoding="utf-8").lower()
    for forbidden in ("openai", "requests", "pixi", "canvas", "react"):
        assert forbidden not in source

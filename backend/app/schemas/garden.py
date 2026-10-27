"""Step 10 本地种植 API 的稳定请求与响应契约。"""

from uuid import UUID

from pydantic import BaseModel, Field

from flower_engine.schema import FlowerRenderSpec, FlowerSpecies, GardenRenderSpec


class PlantFlowerRequest(BaseModel):
    flower_artifact_id: UUID
    x: int = Field(strict=True)
    y: int = Field(strict=True)


class AvailableFlower(BaseModel):
    flower_artifact_id: UUID
    species: FlowerSpecies
    template_id: str
    scale: float = Field(ge=0.75, le=1.25)
    render_spec: FlowerRenderSpec


class GardenPreviewResponse(BaseModel):
    garden: GardenRenderSpec
    available_flowers: tuple[AvailableFlower, ...]


class CreateMemoryRequest(BaseModel):
    garden_id: UUID
    text: str = Field(min_length=1, max_length=2000)
    x: int = Field(strict=True)
    y: int = Field(strict=True)


class RegenerateMusicRequest(BaseModel):
    modification_text: str = Field(min_length=1, max_length=500)


class SelectMusicVersionRequest(BaseModel):
    audio_artifact_id: UUID


class RenameMusicVersionRequest(BaseModel):
    audio_artifact_id: UUID
    display_name: str = Field(min_length=1, max_length=60)


class MusicSuggestionRequest(BaseModel):
    seen_titles: tuple[str, ...] = Field(default=(), max_length=12)

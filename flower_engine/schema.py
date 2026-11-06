"""Flower Engine 使用的稳定花朵视觉、渲染规格与资产契约。"""

from datetime import datetime
import re
from typing import Literal, TypeAlias
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from ai_engine.memory.schema import BEIJING_TIMEZONE


MAX_VARIATION_SEED = (1 << 63) - 1


FlowerSpecies: TypeAlias = Literal[
    "rose",
    "peony",
    "sunflower",
    "tulip",
    "hydrangea",
    "lily",
    "daisy",
    "lavender",
    "wildflower",
    "cosmos",
    "poppy",
    "bellflower",
    "cherry_blossom",
    "camellia",
    "aster",
    "lotus",
]

FlowerPalette: TypeAlias = Literal[
    "deep_crimson",
    "warm_gold",
    "sunlit_yellow",
    "soft_pink",
    "cool_blue",
    "violet_dream",
    "fresh_green",
    "moonlit_white",
    "balanced_pastel",
]

ParticleEffect: TypeAlias = Literal[
    "none",
    "soft_glow",
    "sparkles",
    "petals",
    "fireflies",
    "stardust",
]

FlowerDecoration: TypeAlias = Literal[
    "none",
    "dew_drops",
    "leaf_sprigs",
    "star_charms",
    "light_ribbons",
]

GrowthDirection: TypeAlias = Literal[
    "steady",
    "upright",
    "opening",
    "expanding",
    "rising",
    "releasing",
]

BloomShape: TypeAlias = Literal[
    "rosette",
    "rounded_layered",
    "radial_disc",
    "cup",
    "clustered_sphere",
    "trumpet",
    "spike_cluster",
    "open_cluster",
]

LeafShape: TypeAlias = Literal[
    "serrated",
    "broad_lobed",
    "broad_heart",
    "lance",
    "broad_oval",
    "narrow",
    "mixed",
]

RenderLayer: TypeAlias = Literal[
    "shadow",
    "stem",
    "leaves",
    "bloom_back",
    "bloom_front",
    "decoration",
    "glow",
    "particles",
]

RENDER_LAYER_ORDER: tuple[RenderLayer, ...] = (
    "shadow",
    "stem",
    "leaves",
    "bloom_back",
    "bloom_front",
    "decoration",
    "glow",
    "particles",
)

_HEX_COLOR_PATTERN = re.compile(r"#[0-9A-F]{6}")


class FlowerSpec(BaseModel):
    """由 MusicBlueprint 推导出的、与具体渲染器解耦的花朵视觉规格。"""

    species: FlowerSpecies
    palette: FlowerPalette
    size: float = Field(ge=0, le=1)
    petal_count: int = Field(ge=3, le=16)
    stem_height: float = Field(ge=0, le=1)
    sway_speed: float = Field(ge=0, le=1)
    glow: float = Field(ge=0, le=1)
    particle_effect: ParticleEffect
    decoration: FlowerDecoration
    growth_direction: GrowthDirection


class FlowerVariationSpec(BaseModel):
    """由稳定 seed 生成的、与具体渲染器解耦的花朵个体变化。"""

    variation_seed: int = Field(
        strict=True,
        ge=0,
        le=MAX_VARIATION_SEED,
    )
    petal_length_scale: float = Field(ge=0.90, le=1.10)
    bloom_width_scale: float = Field(ge=0.90, le=1.10)
    stem_curve: float = Field(ge=-1, le=1)
    leaf_count: int = Field(ge=2, le=5)
    leaf_angle_offset: float = Field(ge=-15, le=15)
    color_value_shift: float = Field(ge=-0.08, le=0.08)
    sway_phase: float = Field(ge=0, le=1)
    particle_phase: float = Field(ge=0, le=1)


class FlowerColorSpec(BaseModel):
    """Pixel Renderer 可直接使用的固定十六进制颜色。"""

    petal_primary: str
    petal_secondary: str
    petal_highlight: str
    flower_center: str
    stem: str
    leaf: str
    glow: str
    particle: str

    @field_validator(
        "petal_primary",
        "petal_secondary",
        "petal_highlight",
        "flower_center",
        "stem",
        "leaf",
        "glow",
        "particle",
    )
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        if not _HEX_COLOR_PATTERN.fullmatch(value):
            raise ValueError("颜色必须使用大写 #RRGGBB 格式")
        return value


class FlowerGeometrySpec(BaseModel):
    """与具体像素分辨率解耦的花朵几何参数。"""

    bloom_shape: BloomShape
    leaf_shape: LeafShape
    petal_count: int = Field(ge=3, le=16)
    bloom_scale_x: float = Field(ge=0.50, le=1.50)
    bloom_scale_y: float = Field(ge=0.50, le=1.50)
    stem_height_ratio: float = Field(ge=0, le=1)
    stem_curve: float = Field(ge=-1, le=1)
    leaf_count: int = Field(ge=2, le=5)
    leaf_angle_offset: float = Field(ge=-15, le=15)
    anchor_x: Literal[0.5] = 0.5
    anchor_y: Literal[1.0] = 1.0


class FlowerAnimationSpec(BaseModel):
    """PixiJS 可直接换算为动画时间轴的参数。"""

    sway_amplitude: float = Field(ge=0, le=0.10)
    sway_period_ms: int = Field(strict=True, ge=1200, le=3600)
    sway_phase: float = Field(ge=0, le=1)
    glow_opacity: float = Field(ge=0, le=0.65)
    glow_radius_ratio: float = Field(ge=0, le=0.18)
    particle_rate: float = Field(ge=0, le=5)
    particle_phase: float = Field(ge=0, le=1)


class FlowerRenderSpec(BaseModel):
    """Flower Engine 输出给未来 Pixel Renderer 的版本化完整契约。"""

    renderer_schema_version: Literal["1.0"] = "1.0"
    template_id: str
    species: FlowerSpecies
    variation_seed: int = Field(
        strict=True,
        ge=0,
        le=MAX_VARIATION_SEED,
    )
    colors: FlowerColorSpec
    geometry: FlowerGeometrySpec
    animation: FlowerAnimationSpec
    particle_effect: ParticleEffect
    decoration: FlowerDecoration
    growth_direction: GrowthDirection
    layer_order: tuple[RenderLayer, ...] = RENDER_LAYER_ORDER

    @model_validator(mode="after")
    def validate_renderer_contract(self) -> "FlowerRenderSpec":
        expected_template_id = f"{self.species}_v1"
        if self.template_id != expected_template_id:
            raise ValueError(
                f"template_id 必须为 {expected_template_id}"
            )
        if self.layer_order != RENDER_LAYER_ORDER:
            raise ValueError("layer_order 必须使用 Flower Engine 固定图层顺序")
        return self


class FlowerArtifact(BaseModel):
    """一次正式生成的花朵资产；保存语义与渲染参数的独立快照。"""

    id: UUID = Field(default_factory=uuid4)
    creation_id: UUID | None = None
    species: FlowerSpecies
    variation_seed: int = Field(
        strict=True,
        ge=0,
        le=MAX_VARIATION_SEED,
    )
    flower_spec: FlowerSpec
    render_spec: FlowerRenderSpec
    renderer_schema_version: Literal["1.0"] = "1.0"
    template_id: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @field_validator("flower_spec")
    @classmethod
    def copy_flower_spec_snapshot(cls, value: FlowerSpec) -> FlowerSpec:
        return FlowerSpec.model_validate(value.model_dump())

    @field_validator("render_spec")
    @classmethod
    def copy_render_spec_snapshot(
        cls,
        value: FlowerRenderSpec,
    ) -> FlowerRenderSpec:
        return FlowerRenderSpec.model_validate(value.model_dump())

    @model_validator(mode="after")
    def validate_snapshot_relationship(self) -> "FlowerArtifact":
        if self.species != self.flower_spec.species:
            raise ValueError("species 必须与 flower_spec.species 一致")
        if self.species != self.render_spec.species:
            raise ValueError("species 必须与 render_spec.species 一致")
        if self.variation_seed != self.render_spec.variation_seed:
            raise ValueError("variation_seed 必须与 render_spec 一致")
        if self.renderer_schema_version != self.render_spec.renderer_schema_version:
            raise ValueError("renderer_schema_version 必须与 render_spec 一致")
        if self.template_id != self.render_spec.template_id:
            raise ValueError("template_id 必须与 render_spec 一致")
        return self


class Garden(BaseModel):
    """长期存在的二维整数网格空间，不直接保存花朵或种植记录。"""

    id: UUID = Field(default_factory=uuid4)
    name: str
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @field_validator("name")
    @classmethod
    def reject_blank_garden_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("花园名称不能为空")
        return value


class PlantingRecord(BaseModel):
    """一份 FlowerArtifact 在某个 Garden 网格位置的独立种植记录。"""

    id: UUID = Field(default_factory=uuid4)
    garden_id: UUID
    flower_artifact_id: UUID
    x: int = Field(strict=True, ge=0)
    y: int = Field(strict=True, ge=0)
    placement_schema_version: Literal["legacy", "terrain-v1"] = "legacy"
    flower_size: Literal["small", "large"] = "small"
    occupied_tiles: tuple[tuple[int, int], ...] = ()
    planted_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @model_validator(mode="after")
    def validate_terrain_footprint(self) -> "PlantingRecord":
        if self.placement_schema_version == "legacy":
            if self.flower_size != "small" or self.occupied_tiles:
                raise ValueError("legacy 种植记录必须按 small 且不保存地形占地")
            return self
        expected_count = 1 if self.flower_size == "small" else 9
        if len(self.occupied_tiles) != expected_count:
            raise ValueError(f"{self.flower_size} 花朵占地数量必须为 {expected_count}")
        if len(set(self.occupied_tiles)) != len(self.occupied_tiles):
            raise ValueError("花朵占地不能包含重复格子")
        if (self.x, self.y) not in self.occupied_tiles:
            raise ValueError("花朵中心格必须包含在占地范围内")
        if any(tile_x < 0 or tile_y < 0 for tile_x, tile_y in self.occupied_tiles):
            raise ValueError("花朵占地坐标不能为负数")
        return self


class GardenBackgroundSpec(BaseModel):
    """Garden Renderer 可直接使用的稳定像素背景配置。"""

    style: Literal["meadow"] = "meadow"
    base_color: str = "#294C35"
    tile_color: str = "#315A3D"
    accent_color: str = "#6F8A55"

    @field_validator("base_color", "tile_color", "accent_color")
    @classmethod
    def validate_background_color(cls, value: str) -> str:
        if not _HEX_COLOR_PATTERN.fullmatch(value):
            raise ValueError("背景颜色必须使用大写 #RRGGBB 格式")
        return value


class GardenRenderFlower(BaseModel):
    """一条种植记录转换出的、与存储解耦的花园渲染项。"""

    planting_record_id: UUID
    flower_artifact_id: UUID
    template_id: str
    grid_x: int = Field(strict=True, ge=0)
    grid_y: int = Field(strict=True, ge=0)
    pixel_x: float = Field(ge=0)
    pixel_y: float = Field(ge=0)
    scale: float = Field(ge=0.75, le=1.25)
    z_index: int = Field(strict=True, ge=0)
    placement_schema_version: Literal["legacy", "terrain-v1"] = "legacy"
    flower_size: Literal["small", "large"] = "small"
    occupied_tiles: tuple[tuple[int, int], ...] = ()
    render_spec: FlowerRenderSpec

    @model_validator(mode="after")
    def validate_flower_render_relationship(self) -> "GardenRenderFlower":
        if self.template_id != self.render_spec.template_id:
            raise ValueError("template_id 必须与 render_spec.template_id 一致")
        return self


class GardenRenderSpec(BaseModel):
    """由 Garden Domain 转换出的完整、版本化 Pixi 场景契约。"""

    renderer_schema_version: Literal["1.0"] = "1.0"
    garden_id: UUID
    grid_width: int = Field(strict=True, gt=0)
    grid_height: int = Field(strict=True, gt=0)
    cell_size: int = Field(strict=True, ge=24, le=96)
    pixel_width: int = Field(strict=True, gt=0)
    pixel_height: int = Field(strict=True, gt=0)
    background: GardenBackgroundSpec = Field(default_factory=GardenBackgroundSpec)
    flowers: tuple[GardenRenderFlower, ...]

    @model_validator(mode="after")
    def validate_garden_dimensions(self) -> "GardenRenderSpec":
        if self.pixel_width != self.grid_width * self.cell_size:
            raise ValueError("pixel_width 必须等于 grid_width × cell_size")
        if self.pixel_height != self.grid_height * self.cell_size:
            raise ValueError("pixel_height 必须等于 grid_height × cell_size")
        if tuple(sorted(self.flowers, key=lambda flower: flower.z_index)) != self.flowers:
            raise ValueError("flowers 必须按 z_index 从小到大排列")
        return self


class FlowerReference(BaseModel):
    """一种现实花卉在 MuseGarden 中使用的稳定结构参考。"""

    species: FlowerSpecies
    display_name: str
    bloom_shape: BloomShape
    base_petal_count: int = Field(ge=3, le=16)
    petal_count_range: tuple[int, int]
    base_stem_height: float = Field(ge=0, le=1)
    stem_height_range: tuple[float, float]
    leaf_shape: LeafShape
    supported_palettes: tuple[FlowerPalette, ...] = Field(min_length=1)
    supported_decorations: tuple[FlowerDecoration, ...] = Field(min_length=1)

    @field_validator("display_name")
    @classmethod
    def reject_blank_display_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("花卉显示名称不能为空")
        return value

    @model_validator(mode="after")
    def validate_reference_ranges(self) -> "FlowerReference":
        petal_minimum, petal_maximum = self.petal_count_range
        if not 3 <= petal_minimum <= petal_maximum <= 16:
            raise ValueError("花瓣数量范围必须位于 3-16 且下限不大于上限")
        if not petal_minimum <= self.base_petal_count <= petal_maximum:
            raise ValueError("基础花瓣数量必须位于花瓣数量范围内")

        stem_minimum, stem_maximum = self.stem_height_range
        if not 0 <= stem_minimum <= stem_maximum <= 1:
            raise ValueError("茎高范围必须位于 0-1 且下限不大于上限")
        if not stem_minimum <= self.base_stem_height <= stem_maximum:
            raise ValueError("基础茎高必须位于茎高范围内")

        if len(set(self.supported_palettes)) != len(self.supported_palettes):
            raise ValueError("支持的色调不能重复")
        if len(set(self.supported_decorations)) != len(
            self.supported_decorations
        ):
            raise ValueError("支持的装饰不能重复")
        return self

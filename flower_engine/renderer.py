"""将花朵语义、现实参考与个体变化组合为稳定渲染契约。"""

from flower_engine.reference_library import (
    constrain_flower_spec,
    get_flower_reference,
)
from flower_engine.schema import (
    RENDER_LAYER_ORDER,
    FlowerAnimationSpec,
    FlowerColorSpec,
    FlowerGeometrySpec,
    FlowerPalette,
    FlowerRenderSpec,
    FlowerSpec,
    FlowerVariationSpec,
    ParticleEffect,
)
from flower_engine.variation import build_flower_variation


_STEM_COLOR = "#47704B"
_LEAF_COLOR = "#5F8A58"

_PIXEL_PALETTES: dict[FlowerPalette, dict[str, str]] = {
    "deep_crimson": {
        "petal_primary": "#A83A5B",
        "petal_secondary": "#6F2845",
        "petal_highlight": "#E5738C",
        "flower_center": "#F1B24A",
        "glow": "#E9899E",
        "particle": "#F4A7B7",
    },
    "warm_gold": {
        "petal_primary": "#D9A441",
        "petal_secondary": "#9E6B2F",
        "petal_highlight": "#F5D06F",
        "flower_center": "#7A4F27",
        "glow": "#F7D77A",
        "particle": "#FFE5A3",
    },
    "sunlit_yellow": {
        "petal_primary": "#E7B93F",
        "petal_secondary": "#B67A2E",
        "petal_highlight": "#FFE27A",
        "flower_center": "#6E512A",
        "glow": "#FFE89C",
        "particle": "#FFF1B8",
    },
    "soft_pink": {
        "petal_primary": "#D98BA6",
        "petal_secondary": "#A85E7E",
        "petal_highlight": "#F4B5C7",
        "flower_center": "#E2B04C",
        "glow": "#F7C8D5",
        "particle": "#FFE0E8",
    },
    "cool_blue": {
        "petal_primary": "#6F8FC6",
        "petal_secondary": "#4F6596",
        "petal_highlight": "#A8C4E8",
        "flower_center": "#E2C66D",
        "glow": "#BFD7F2",
        "particle": "#D9E9FA",
    },
    "violet_dream": {
        "petal_primary": "#8D73BF",
        "petal_secondary": "#654E95",
        "petal_highlight": "#B9A3E0",
        "flower_center": "#E0B95E",
        "glow": "#CDBEF0",
        "particle": "#E4D9FA",
    },
    "fresh_green": {
        "petal_primary": "#78A96B",
        "petal_secondary": "#527B4D",
        "petal_highlight": "#A8CF8B",
        "flower_center": "#E1C65B",
        "glow": "#B9DDA4",
        "particle": "#D6EDC7",
    },
    "moonlit_white": {
        "petal_primary": "#DDE3E8",
        "petal_secondary": "#AAB7C4",
        "petal_highlight": "#F7F8F4",
        "flower_center": "#D8BD66",
        "glow": "#F4F6F8",
        "particle": "#FFFFFF",
    },
    "balanced_pastel": {
        "petal_primary": "#B89BCB",
        "petal_secondary": "#7E8FB3",
        "petal_highlight": "#E5B5C9",
        "flower_center": "#D8B85A",
        "glow": "#DDCEE8",
        "particle": "#F0DFEA",
    },
}

_PARTICLE_RATES: dict[ParticleEffect, float] = {
    "none": 0.0,
    "soft_glow": 0.0,
    "sparkles": 3.5,
    "petals": 1.5,
    "fireflies": 2.0,
    "stardust": 5.0,
}


def _shift_color(color: str, value_shift: float) -> str:
    """对 #RRGGBB 进行有界的 RGB 明暗平移。"""
    delta = round(value_shift * 255)
    channels = (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )
    shifted = tuple(min(255, max(0, channel + delta)) for channel in channels)
    return "#" + "".join(f"{channel:02X}" for channel in shifted)


def _build_colors(
    palette: FlowerPalette,
    value_shift: float,
) -> FlowerColorSpec:
    base_colors = _PIXEL_PALETTES[palette]
    return FlowerColorSpec(
        petal_primary=_shift_color(base_colors["petal_primary"], value_shift),
        petal_secondary=_shift_color(
            base_colors["petal_secondary"],
            value_shift,
        ),
        petal_highlight=_shift_color(
            base_colors["petal_highlight"],
            value_shift,
        ),
        flower_center=base_colors["flower_center"],
        stem=_STEM_COLOR,
        leaf=_LEAF_COLOR,
        glow=_shift_color(base_colors["glow"], value_shift),
        particle=_shift_color(base_colors["particle"], value_shift),
    )


def build_flower_render_spec(
    spec: FlowerSpec,
    variation: FlowerVariationSpec,
) -> FlowerRenderSpec:
    """构建无需理解情绪语义即可消费的版本化渲染规格。"""
    if not isinstance(spec, FlowerSpec):
        raise TypeError("spec 必须是 FlowerSpec 实例")
    if not isinstance(variation, FlowerVariationSpec):
        raise TypeError("variation 必须是 FlowerVariationSpec 实例")

    constrained_spec = constrain_flower_spec(spec)
    expected_variation = build_flower_variation(
        constrained_spec,
        variation.variation_seed,
    )
    if variation != expected_variation:
        raise ValueError("variation 与当前 FlowerSpec 的 species 或 seed 不一致")

    reference = get_flower_reference(constrained_spec.species)
    base_bloom_scale = 0.75 + constrained_spec.size * 0.50

    colors = _build_colors(
        constrained_spec.palette,
        variation.color_value_shift,
    )
    geometry = FlowerGeometrySpec(
        bloom_shape=reference.bloom_shape,
        leaf_shape=reference.leaf_shape,
        petal_count=constrained_spec.petal_count,
        bloom_scale_x=round(
            base_bloom_scale * variation.bloom_width_scale,
            4,
        ),
        bloom_scale_y=round(
            base_bloom_scale * variation.petal_length_scale,
            4,
        ),
        stem_height_ratio=constrained_spec.stem_height,
        stem_curve=variation.stem_curve,
        leaf_count=variation.leaf_count,
        leaf_angle_offset=variation.leaf_angle_offset,
    )
    animation = FlowerAnimationSpec(
        sway_amplitude=round(
            0.02 + constrained_spec.sway_speed * 0.06,
            4,
        ),
        sway_period_ms=round(
            3600 - constrained_spec.sway_speed * 2400
        ),
        sway_phase=variation.sway_phase,
        glow_opacity=round(constrained_spec.glow * 0.65, 4),
        glow_radius_ratio=round(constrained_spec.glow * 0.18, 4),
        particle_rate=_PARTICLE_RATES[constrained_spec.particle_effect],
        particle_phase=variation.particle_phase,
    )

    return FlowerRenderSpec(
        template_id=f"{constrained_spec.species}_v1",
        species=constrained_spec.species,
        variation_seed=variation.variation_seed,
        colors=colors,
        geometry=geometry,
        animation=animation,
        particle_effect=constrained_spec.particle_effect,
        decoration=constrained_spec.decoration,
        growth_direction=constrained_spec.growth_direction,
        layer_order=RENDER_LAYER_ORDER,
    )

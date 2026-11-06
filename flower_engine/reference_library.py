"""MuseGarden 首版现实花卉参考库及 FlowerSpec 约束规则。"""

from typing import get_args

from flower_engine.schema import (
    FlowerDecoration,
    FlowerPalette,
    FlowerReference,
    FlowerSpecies,
    FlowerSpec,
)


_ALL_PALETTES: tuple[FlowerPalette, ...] = get_args(FlowerPalette)
_ALL_DECORATIONS: tuple[FlowerDecoration, ...] = get_args(FlowerDecoration)


FLOWER_REFERENCES: dict[FlowerSpecies, FlowerReference] = {
    "rose": FlowerReference(
        species="rose",
        display_name="玫瑰",
        bloom_shape="rosette",
        base_petal_count=12,
        petal_count_range=(8, 16),
        base_stem_height=0.70,
        stem_height_range=(0.55, 0.90),
        leaf_shape="serrated",
        supported_palettes=(
            "deep_crimson",
            "soft_pink",
            "violet_dream",
            "moonlit_white",
            "warm_gold",
        ),
        supported_decorations=(
            "none",
            "dew_drops",
            "leaf_sprigs",
            "light_ribbons",
        ),
    ),
    "peony": FlowerReference(
        species="peony",
        display_name="牡丹",
        bloom_shape="rounded_layered",
        base_petal_count=14,
        petal_count_range=(10, 16),
        base_stem_height=0.62,
        stem_height_range=(0.45, 0.78),
        leaf_shape="broad_lobed",
        supported_palettes=(
            "warm_gold",
            "soft_pink",
            "deep_crimson",
            "moonlit_white",
            "violet_dream",
        ),
        supported_decorations=(
            "none",
            "dew_drops",
            "star_charms",
            "light_ribbons",
        ),
    ),
    "sunflower": FlowerReference(
        species="sunflower",
        display_name="向日葵",
        bloom_shape="radial_disc",
        base_petal_count=14,
        petal_count_range=(10, 16),
        base_stem_height=0.82,
        stem_height_range=(0.65, 0.95),
        leaf_shape="broad_heart",
        supported_palettes=(
            "sunlit_yellow",
            "warm_gold",
            "soft_pink",
            "deep_crimson",
        ),
        supported_decorations=(
            "none",
            "leaf_sprigs",
            "star_charms",
            "light_ribbons",
        ),
    ),
    "tulip": FlowerReference(
        species="tulip",
        display_name="郁金香",
        bloom_shape="cup",
        base_petal_count=6,
        petal_count_range=(5, 8),
        base_stem_height=0.72,
        stem_height_range=(0.55, 0.90),
        leaf_shape="lance",
        supported_palettes=(
            "warm_gold",
            "soft_pink",
            "deep_crimson",
            "moonlit_white",
            "violet_dream",
            "sunlit_yellow",
            "cool_blue",
        ),
        supported_decorations=(
            "none",
            "dew_drops",
            "leaf_sprigs",
            "light_ribbons",
        ),
    ),
    "hydrangea": FlowerReference(
        species="hydrangea",
        display_name="绣球",
        bloom_shape="clustered_sphere",
        base_petal_count=14,
        petal_count_range=(10, 16),
        base_stem_height=0.60,
        stem_height_range=(0.45, 0.78),
        leaf_shape="broad_oval",
        supported_palettes=(
            "cool_blue",
            "violet_dream",
            "soft_pink",
            "moonlit_white",
            "fresh_green",
        ),
        supported_decorations=(
            "none",
            "dew_drops",
            "leaf_sprigs",
            "star_charms",
        ),
    ),
    "lily": FlowerReference(
        species="lily",
        display_name="百合",
        bloom_shape="trumpet",
        base_petal_count=6,
        petal_count_range=(5, 7),
        base_stem_height=0.75,
        stem_height_range=(0.58, 0.92),
        leaf_shape="lance",
        supported_palettes=(
            "moonlit_white",
            "soft_pink",
            "warm_gold",
            "violet_dream",
            "sunlit_yellow",
            "cool_blue",
        ),
        supported_decorations=(
            "none",
            "dew_drops",
            "leaf_sprigs",
            "light_ribbons",
        ),
    ),
    "daisy": FlowerReference(
        species="daisy",
        display_name="雏菊",
        bloom_shape="radial_disc",
        base_petal_count=10,
        petal_count_range=(8, 14),
        base_stem_height=0.58,
        stem_height_range=(0.40, 0.82),
        leaf_shape="narrow",
        supported_palettes=(
            "moonlit_white",
            "sunlit_yellow",
            "soft_pink",
            "cool_blue",
            "fresh_green",
        ),
        supported_decorations=(
            "none",
            "leaf_sprigs",
            "star_charms",
            "dew_drops",
        ),
    ),
    "lavender": FlowerReference(
        species="lavender",
        display_name="薰衣草",
        bloom_shape="spike_cluster",
        base_petal_count=8,
        petal_count_range=(6, 12),
        base_stem_height=0.72,
        stem_height_range=(0.52, 0.92),
        leaf_shape="narrow",
        supported_palettes=(
            "violet_dream",
            "cool_blue",
            "soft_pink",
            "moonlit_white",
        ),
        supported_decorations=(
            "none",
            "dew_drops",
            "star_charms",
            "leaf_sprigs",
        ),
    ),
    "wildflower": FlowerReference(
        species="wildflower",
        display_name="野花",
        bloom_shape="open_cluster",
        base_petal_count=8,
        petal_count_range=(5, 14),
        base_stem_height=0.60,
        stem_height_range=(0.35, 0.88),
        leaf_shape="mixed",
        supported_palettes=_ALL_PALETTES,
        supported_decorations=_ALL_DECORATIONS,
    ),
}

for species, source, name in (
    ("cosmos", "daisy", "波斯菊"),
    ("poppy", "tulip", "虞美人"),
    ("bellflower", "lily", "风铃草"),
    ("cherry_blossom", "wildflower", "樱花"),
    ("camellia", "rose", "山茶花"),
    ("aster", "daisy", "紫苑"),
    ("lotus", "lily", "莲花"),
):
    FLOWER_REFERENCES[species] = FLOWER_REFERENCES[source].model_copy(
        update={"species": species, "display_name": name}, deep=True
    )


def get_flower_reference(species: FlowerSpecies | str) -> FlowerReference:
    """按稳定 species token 查询花卉参考，并返回独立数据副本。"""
    try:
        reference = FLOWER_REFERENCES[species]  # type: ignore[index]
    except (KeyError, TypeError) as error:
        raise ValueError(f"不支持的花卉种类：{species}") from error
    return reference.model_copy(deep=True)


def constrain_flower_spec(spec: FlowerSpec) -> FlowerSpec:
    """将视觉规格限制在对应现实花型可识别的结构范围内。"""
    if not isinstance(spec, FlowerSpec):
        raise TypeError("spec 必须是 FlowerSpec 实例")

    reference = FLOWER_REFERENCES[spec.species]
    petal_minimum, petal_maximum = reference.petal_count_range
    stem_minimum, stem_maximum = reference.stem_height_range

    palette = spec.palette
    if palette not in reference.supported_palettes:
        palette = reference.supported_palettes[0]

    decoration = spec.decoration
    if decoration not in reference.supported_decorations:
        decoration = (
            "none"
            if "none" in reference.supported_decorations
            else reference.supported_decorations[0]
        )

    return spec.model_copy(
        update={
            "palette": palette,
            "petal_count": min(petal_maximum, max(petal_minimum, spec.petal_count)),
            "stem_height": round(
                min(stem_maximum, max(stem_minimum, spec.stem_height)),
                2,
            ),
            "decoration": decoration,
        },
        deep=True,
    )

"""根据 FlowerSpec 与显式 seed 构建可复现的花朵个体变化。"""

from hashlib import sha256

from flower_engine.schema import (
    MAX_VARIATION_SEED,
    FlowerSpec,
    FlowerVariationSpec,
)


_VARIATION_ALGORITHM_VERSION = "musegarden-flower-variation-v1"
_UINT64_RANGE = 1 << 64


def _unit_value(species: str, variation_seed: int, parameter: str) -> float:
    """把稳定身份和参数名映射为 [0, 1) 的跨进程稳定数值。"""
    payload = (
        f"{_VARIATION_ALGORITHM_VERSION}|{species}|"
        f"{variation_seed}|{parameter}"
    ).encode("utf-8")
    digest = sha256(payload).digest()
    return int.from_bytes(digest[:8], byteorder="big") / _UINT64_RANGE


def _map_range(
    species: str,
    variation_seed: int,
    parameter: str,
    minimum: float,
    maximum: float,
    digits: int,
) -> float:
    unit_value = _unit_value(species, variation_seed, parameter)
    return round(minimum + unit_value * (maximum - minimum), digits)


def build_flower_variation(
    spec: FlowerSpec,
    variation_seed: int,
) -> FlowerVariationSpec:
    """为一份 FlowerSpec 构建不改变其语义的稳定个体变化。"""
    if not isinstance(spec, FlowerSpec):
        raise TypeError("spec 必须是 FlowerSpec 实例")
    if not isinstance(variation_seed, int) or isinstance(variation_seed, bool):
        raise TypeError("variation_seed 必须是整数")
    if not 0 <= variation_seed <= MAX_VARIATION_SEED:
        raise ValueError(
            f"variation_seed 必须位于 0-{MAX_VARIATION_SEED}"
        )

    species = spec.species
    leaf_count = 2 + int(
        _unit_value(species, variation_seed, "leaf_count") * 4
    )

    return FlowerVariationSpec(
        variation_seed=variation_seed,
        petal_length_scale=_map_range(
            species,
            variation_seed,
            "petal_length_scale",
            0.90,
            1.10,
            4,
        ),
        bloom_width_scale=_map_range(
            species,
            variation_seed,
            "bloom_width_scale",
            0.90,
            1.10,
            4,
        ),
        stem_curve=_map_range(
            species,
            variation_seed,
            "stem_curve",
            -1.0,
            1.0,
            4,
        ),
        leaf_count=leaf_count,
        leaf_angle_offset=_map_range(
            species,
            variation_seed,
            "leaf_angle_offset",
            -15.0,
            15.0,
            2,
        ),
        color_value_shift=_map_range(
            species,
            variation_seed,
            "color_value_shift",
            -0.08,
            0.08,
            4,
        ),
        sway_phase=_map_range(
            species,
            variation_seed,
            "sway_phase",
            0.0,
            1.0,
            6,
        ),
        particle_phase=_map_range(
            species,
            variation_seed,
            "particle_phase",
            0.0,
            1.0,
            6,
        ),
    )

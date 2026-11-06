"""将 AI Engine 的 MusicBlueprint 确定性转换为 Flower Engine 输入。"""

from ai_engine.blueprint.progression import Progression
from ai_engine.blueprint.schema import MusicBlueprint
from hashlib import sha256
from typing import get_args

from flower_engine.reference_library import constrain_flower_spec
from flower_engine.schema import (
    FlowerDecoration,
    FlowerPalette,
    FlowerSpecies,
    FlowerSpec,
    GrowthDirection,
    ParticleEffect,
)


_TEXTURE_SPECIES: dict[str, FlowerSpecies] = {
    "warm": "tulip",
    "soft": "lily",
    "bright": "sunflower",
    "joyful": "daisy",
    "dreamy": "lavender",
    "ethereal": "lavender",
    "dark": "rose",
    "dramatic": "rose",
    "cinematic": "peony",
    "calm": "hydrangea",
    "delicate": "hydrangea",
    "fresh": "tulip",
    "温暖": "tulip",
    "柔和": "lily",
    "明亮": "sunflower",
    "欢快": "daisy",
    "梦幻": "lavender",
    "空灵": "lavender",
    "黑暗": "rose",
    "戏剧感": "rose",
    "电影感": "peony",
    "平静": "hydrangea",
    "细腻": "hydrangea",
    "清新": "tulip",
}

_EMOTION_SPECIES: dict[str, FlowerSpecies] = {
    "achievement": "peony",
    "satisfaction": "peony",
    "joy": "sunflower",
    "happiness": "daisy",
    "relief": "tulip",
    "calm": "lily",
    "relaxation": "lavender",
    "hope": "sunflower",
    "anxiety": "hydrangea",
    "tension": "rose",
    "sadness": "hydrangea",
    "loneliness": "lavender",
    "anger": "rose",
    "love": "rose",
    "成就感": "peony",
    "满足感": "peony",
    "喜悦": "sunflower",
    "快乐": "daisy",
    "释然": "tulip",
    "平静": "lily",
    "放松": "lavender",
    "希望": "sunflower",
    "焦虑": "hydrangea",
    "紧张": "rose",
    "悲伤": "hydrangea",
    "孤独": "lavender",
    "愤怒": "rose",
    "爱": "rose",
}

_EMOTION_PALETTES: dict[str, FlowerPalette] = {
    "achievement": "warm_gold",
    "satisfaction": "warm_gold",
    "joy": "sunlit_yellow",
    "happiness": "sunlit_yellow",
    "relief": "fresh_green",
    "calm": "cool_blue",
    "relaxation": "violet_dream",
    "hope": "sunlit_yellow",
    "anxiety": "moonlit_white",
    "tension": "deep_crimson",
    "sadness": "cool_blue",
    "loneliness": "violet_dream",
    "anger": "deep_crimson",
    "love": "soft_pink",
    "成就感": "warm_gold",
    "满足感": "warm_gold",
    "喜悦": "sunlit_yellow",
    "快乐": "sunlit_yellow",
    "释然": "fresh_green",
    "平静": "cool_blue",
    "放松": "violet_dream",
    "希望": "sunlit_yellow",
    "焦虑": "moonlit_white",
    "紧张": "deep_crimson",
    "悲伤": "cool_blue",
    "孤独": "violet_dream",
    "愤怒": "deep_crimson",
    "爱": "soft_pink",
}

_EMOTION_DECORATIONS: dict[str, FlowerDecoration] = {
    "achievement": "light_ribbons",
    "satisfaction": "light_ribbons",
    "joy": "star_charms",
    "happiness": "star_charms",
    "relief": "dew_drops",
    "calm": "dew_drops",
    "relaxation": "leaf_sprigs",
    "hope": "star_charms",
    "anxiety": "dew_drops",
    "sadness": "dew_drops",
    "loneliness": "star_charms",
    "成就感": "light_ribbons",
    "满足感": "light_ribbons",
    "喜悦": "star_charms",
    "快乐": "star_charms",
    "释然": "dew_drops",
    "平静": "dew_drops",
    "放松": "leaf_sprigs",
    "希望": "star_charms",
    "焦虑": "dew_drops",
    "悲伤": "dew_drops",
    "孤独": "star_charms",
}

_PROGRESSION_VISUALS: dict[
    Progression,
    tuple[GrowthDirection, ParticleEffect],
] = {
    "steady": ("steady", "none"),
    "calm": ("steady", "soft_glow"),
    "calm_to_rising": ("rising", "sparkles"),
    "quiet_to_bright": ("opening", "soft_glow"),
    "restrained_to_open": ("opening", "sparkles"),
    "gentle_to_bright": ("opening", "soft_glow"),
    "slow_build": ("rising", "none"),
    "gentle_to_climax": ("rising", "sparkles"),
    "building_to_peak": ("rising", "sparkles"),
    "intimate_to_expansive": ("expanding", "stardust"),
    "sparse_to_full": ("expanding", "petals"),
    "soft_to_emotional": ("opening", "petals"),
    "rising_to_release": ("releasing", "sparkles"),
    "tension_to_release": ("releasing", "petals"),
    "reflective_to_resolved": ("upright", "soft_glow"),
    "dark_to_hopeful": ("rising", "fireflies"),
    "melancholic_to_warm": ("opening", "soft_glow"),
    "energetic_to_triumphant": ("upright", "sparkles"),
}

_GLOW_TEXTURE_ADJUSTMENTS = {
    "bright": 0.15,
    "dreamy": 0.15,
    "ethereal": 0.15,
    "明亮": 0.15,
    "梦幻": 0.15,
    "空灵": 0.15,
    "dark": -0.10,
    "黑暗": -0.10,
}

# 附属情绪只微调光感，不覆盖主要情绪选出的花型与色系。
_SECONDARY_GLOW_ADJUSTMENTS = {
    "joy": 0.04,
    "喜悦": 0.04,
    "hope": 0.04,
    "希望": 0.04,
    "sadness": -0.04,
    "悲伤": -0.04,
    "anxiety": -0.04,
    "焦虑": -0.04,
}

# 场景只表达记忆中的环境光，不参与音频分析或花型选择。
_SCENE_GLOW_ADJUSTMENTS = {
    "sunny_afternoon": 0.08,
    "晴朗午后": 0.08,
    "late_night": -0.08,
    "深夜": -0.08,
    "quiet_room": -0.04,
    "安静的房间": -0.04,
}


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return min(maximum, max(minimum, value))


def _select_species(blueprint: MusicBlueprint) -> FlowerSpecies:
    texture = _normalize(blueprint.texture)
    emotion = _normalize(blueprint.primary_emotion)
    if texture in _TEXTURE_SPECIES:
        return _TEXTURE_SPECIES[texture]
    if emotion in _EMOTION_SPECIES:
        return _EMOTION_SPECIES[emotion]
    return next(
        (
            _EMOTION_SPECIES[secondary]
            for secondary in map(_normalize, blueprint.secondary_emotions)
            if secondary in _EMOTION_SPECIES
        ),
        "wildflower",
    )


def _select_palette(blueprint: MusicBlueprint) -> FlowerPalette:
    emotion = _normalize(blueprint.primary_emotion)
    known_palette = _EMOTION_PALETTES.get(emotion)
    if known_palette is not None:
        return known_palette

    for secondary in map(_normalize, blueprint.secondary_emotions):
        if secondary in _EMOTION_PALETTES:
            return _EMOTION_PALETTES[secondary]

    if blueprint.valence < 0.20:
        return "deep_crimson"
    if blueprint.valence < 0.40:
        return "cool_blue"
    if blueprint.valence < 0.60:
        return "balanced_pastel"
    if blueprint.valence < 0.80:
        return "soft_pink"
    return "sunlit_yellow"


def _petal_count(blueprint: MusicBlueprint) -> int:
    energy_layers = int(blueprint.energy * 6 + 0.5)
    instrument_layers = min(len(blueprint.instruments), 3)
    return min(16, max(3, 4 + energy_layers + instrument_layers))


def _sway_speed(tempo: int) -> float:
    bounded_tempo = min(180, max(40, tempo))
    return round(0.15 + ((bounded_tempo - 40) / 140) * 0.75, 2)


def _glow(blueprint: MusicBlueprint) -> float:
    texture = _normalize(blueprint.texture)
    adjustment = _GLOW_TEXTURE_ADJUSTMENTS.get(texture, 0.0)
    secondary_adjustment = sum(
        _SECONDARY_GLOW_ADJUSTMENTS.get(_normalize(emotion), 0.0)
        for emotion in blueprint.secondary_emotions
    )
    secondary_adjustment = min(0.08, max(-0.08, secondary_adjustment))
    scene_adjustment = _SCENE_GLOW_ADJUSTMENTS.get(
        _normalize(blueprint.scene), 0.0
    )
    return round(
        _clamp(
            blueprint.valence * 0.70
            + adjustment
            + secondary_adjustment
            + scene_adjustment
        ),
        2,
    )


def blueprint_to_flower_spec(blueprint: MusicBlueprint, variation_seed: int | None = None) -> FlowerSpec:
    """创建不依赖 LLM、网络、数据库或渲染器的花朵视觉规格。"""
    if not isinstance(blueprint, MusicBlueprint):
        raise TypeError("blueprint 必须是 MusicBlueprint 实例")

    growth_direction, particle_effect = _PROGRESSION_VISUALS[
        blueprint.progression
    ]
    emotion = _normalize(blueprint.primary_emotion)

    species = _select_species(blueprint)
    if variation_seed is not None:
        candidates = get_args(FlowerSpecies)
        digest = sha256(str(variation_seed).encode()).digest()
        species = candidates[int.from_bytes(digest[:8], "big") % len(candidates)]

    raw_spec = FlowerSpec(
        species=species,
        palette=_select_palette(blueprint),
        size=round(0.40 + blueprint.energy * 0.55, 2),
        petal_count=_petal_count(blueprint),
        stem_height=round(0.45 + blueprint.energy * 0.45, 2),
        sway_speed=_sway_speed(blueprint.tempo),
        glow=_glow(blueprint),
        particle_effect=particle_effect,
        decoration=_EMOTION_DECORATIONS.get(emotion, "none"),
        growth_direction=growth_direction,
    )
    return constrain_flower_spec(raw_spec)

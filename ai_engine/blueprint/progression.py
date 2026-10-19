"""MusicBlueprint 中音乐发展标签的唯一正式定义。"""

from typing import Literal, TypeAlias, get_args


Progression: TypeAlias = Literal[
    "steady",
    "calm",
    "calm_to_rising",
    "quiet_to_bright",
    "restrained_to_open",
    "gentle_to_bright",
    "slow_build",
    "gentle_to_climax",
    "building_to_peak",
    "intimate_to_expansive",
    "sparse_to_full",
    "soft_to_emotional",
    "rising_to_release",
    "tension_to_release",
    "reflective_to_resolved",
    "dark_to_hopeful",
    "melancholic_to_warm",
    "energetic_to_triumphant",
]

# Schema、Prompt、Adapter 与测试均从此常量读取标签列表。
PROGRESSION_VALUES: tuple[Progression, ...] = get_args(Progression)

PROGRESSION_DESCRIPTIONS: dict[Progression, str] = {
    "steady": "整体保持平稳、均衡，适合持续陪伴或专注。",
    "calm": "全程安静、克制、舒缓，适合休息或内省。",
    "calm_to_rising": "从平静开始，逐渐变得明亮、有向上感。",
    "quiet_to_bright": "从安静、轻柔开始，逐渐走向明亮。",
    "restrained_to_open": "从克制内敛开始，逐渐打开并更具表达力。",
    "gentle_to_bright": "从温柔开始，逐渐变得轻快、明亮。",
    "slow_build": "缓慢累积层次与动力，不急于形成高潮。",
    "gentle_to_climax": "从柔和开始，逐步建立到情感高潮。",
    "building_to_peak": "持续增强力度和密度，并达到清晰的高点。",
    "intimate_to_expansive": "从亲密、近距离的表达逐渐扩展为开阔感。",
    "sparse_to_full": "从稀疏简约的编配，逐渐发展为丰满层次。",
    "soft_to_emotional": "从轻柔克制开始，逐渐加强情感表达。",
    "rising_to_release": "逐渐上扬累积，最后获得释然或释放。",
    "tension_to_release": "先保留紧张感，再逐步化解和释放。",
    "reflective_to_resolved": "从反思、沉静开始，最终形成坚定的落点。",
    "dark_to_hopeful": "从暗淡或低落的色彩，逐渐走向希望。",
    "melancholic_to_warm": "从忧伤感开始，逐渐变得温暖、被安慰。",
    "energetic_to_triumphant": "保持活力并持续推进，最终达到胜利或庆祝感。",
}

PROGRESSION_CAPTIONS: dict[Progression, str] = {
    "steady": "Keep a steady and balanced musical development.",
    "calm": "Maintain a calm, restrained, and soothing development throughout.",
    "calm_to_rising": "Begin calmly and gradually become brighter and more uplifting.",
    "quiet_to_bright": "Begin quietly and gently, then gradually become brighter.",
    "restrained_to_open": "Begin restrained and gradually become more open and expressive.",
    "gentle_to_bright": "Begin gently and gradually become lighter and brighter.",
    "slow_build": "Build layers and momentum slowly without rushing toward a climax.",
    "gentle_to_climax": "Begin gently and gradually build toward an emotional climax.",
    "building_to_peak": "Continuously increase intensity and density toward a clear peak.",
    "intimate_to_expansive": "Begin intimate and close, then gradually expand into an open soundscape.",
    "sparse_to_full": "Begin with sparse instrumentation and gradually grow into a fuller arrangement.",
    "soft_to_emotional": "Begin soft and restrained, then gradually deepen the emotional expression.",
    "rising_to_release": "Gradually rise in intensity and resolve with a sense of release.",
    "tension_to_release": "Hold gentle tension at first, then gradually resolve and release it.",
    "reflective_to_resolved": "Begin reflective and contemplative, then arrive at a clear sense of resolution.",
    "dark_to_hopeful": "Move from a dark, subdued color toward a hopeful sense of light.",
    "melancholic_to_warm": "Begin melancholic and gradually become warmer and more comforting.",
    "energetic_to_triumphant": "Sustain energetic forward motion and arrive at a triumphant, celebratory finish.",
}

PROGRESSION_PROMPT_GUIDE = "\n".join(
    f"- {value}: {PROGRESSION_DESCRIPTIONS[value]}" for value in PROGRESSION_VALUES
)

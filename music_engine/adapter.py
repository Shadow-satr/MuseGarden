"""将 AI Engine 的 MusicBlueprint 确定性转换为 Music Engine 输入。"""

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.blueprint.progression import PROGRESSION_CAPTIONS

from music_engine.schema import MusicGenerationSpec


_EMOTION_TRANSLATIONS = {
    "满足感": "satisfaction",
    "成就感": "achievement",
    "疲劳": "slight tiredness",
    "喜悦": "joy",
    "快乐": "joy",
    "释然": "relief",
    "平静": "calm",
    "放松": "relaxation",
    "希望": "hope",
    "焦虑": "anxiety",
    "紧张": "tension",
    "悲伤": "sadness",
    "孤独": "loneliness",
    "愤怒": "anger",
}

_INSTRUMENT_TRANSLATIONS = {
    "钢琴": "piano",
    "吉他": "guitar",
    "木吉他": "acoustic guitar",
    "弦乐": "strings",
    "小提琴": "violin",
    "大提琴": "cello",
    "长笛": "flute",
    "鼓": "drums",
    "贝斯": "bass",
    "合成器": "synthesizer",
}

_TEXTURE_TRANSLATIONS = {
    "温暖": "warm",
    "柔和": "soft",
    "明亮": "bright",
    "电影感": "cinematic",
    "梦幻": "dreamy",
    "空灵": "ethereal",
    "黑暗": "dark",
}

def _safe_text(value: str, translations: dict[str, str]) -> str:
    """翻译项目常用值；未知自由文本保持可读，且不影响转换流程。"""
    normalized = value.strip()
    return translations.get(normalized, normalized.replace("_", " ").replace("-", " "))


def _natural_list(values: list[str]) -> str:
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _energy_description(energy: float) -> str:
    """把 MuseGarden 的连续语义坐标近似映射为五档提示词。"""
    if energy < 0.20:
        return "Very low energy"
    if energy < 0.40:
        return "Low energy"
    if energy < 0.60:
        return "Moderate energy"
    if energy < 0.80:
        return "High energy"
    return "Very high energy"


def _valence_description(valence: float) -> str:
    """把 MuseGarden 的连续情绪倾向近似映射为五档提示词。"""
    if valence < 0.20:
        return "a deeply melancholic and dark emotional tone"
    if valence < 0.40:
        return "a somewhat melancholic emotional tone"
    if valence < 0.60:
        return "a balanced and neutral emotional tone"
    if valence < 0.80:
        return "a warm and positive emotional tone"
    return "a strongly uplifting and joyful emotional tone"


def _build_caption(blueprint: MusicBlueprint) -> str:
    texture = _safe_text(blueprint.texture, _TEXTURE_TRANSLATIONS)
    instruments = [_safe_text(item, _INSTRUMENT_TRANSLATIONS) for item in blueprint.instruments]
    primary_emotion = _safe_text(blueprint.primary_emotion, _EMOTION_TRANSLATIONS)
    progression = PROGRESSION_CAPTIONS[blueprint.progression]

    opening = f"{texture.capitalize()} instrumental music"
    if instruments:
        opening += f" with {_natural_list(instruments)}"
    opening += "."

    # scene 与 secondary_emotions 保留在 Blueprint / Memory 中。它们目前不作为
    # 音乐模型的核心控制信息，避免把用户经历或过多语义塞进第一版 caption。
    feeling = f"A feeling of {primary_emotion} with {_valence_description(blueprint.valence)}."

    return " ".join((opening, feeling, f"{_energy_description(blueprint.energy)}.", progression))


def blueprint_to_generation_spec(
    blueprint: MusicBlueprint,
    duration_seconds: int = 20,
    seed: int | None = None,
) -> MusicGenerationSpec:
    """创建不依赖 LLM、HTTP 或 Provider 的可序列化音乐生成规格。"""
    if not isinstance(blueprint, MusicBlueprint):
        raise TypeError("blueprint 必须是 MusicBlueprint 实例")

    return MusicGenerationSpec(
        caption=_build_caption(blueprint),
        duration_seconds=duration_seconds,
        bpm=blueprint.tempo,
        key=blueprint.key,
        instrumental=True,
        seed=seed,
    )

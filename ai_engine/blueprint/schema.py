"""
定义 Music Blueprint 数据结构。

Music Blueprint 是 MuseGarden 中 AI 生成音乐前的结构化描述，
用于连接：

用户语义理解
        ↓
音乐生成模块
        ↓
花朵生成模块
        ↓
用户记忆系统
"""

from pydantic import BaseModel, Field

from ai_engine.blueprint.progression import Progression


class MusicBlueprint(BaseModel):
    """
    AI生成音乐前的结构化音乐描述。
    """

    # =========================
    # 情绪信息
    # =========================

    arrangement: str = ""
    rhythm: str = ""
    section_development: str = ""
    ending: str = ""

    primary_emotion: str
    """
    用户当前最主要的情绪。
    例如：
    achievement
    joy
    relief
    """

    secondary_emotions: list[str]
    """
    用户伴随出现的其他情绪。
    可以包含多个情绪标签。
    """


    # =========================
    # 情绪强度
    # =========================

    energy: float = Field(
        ge=0,
        le=1
    )
    """
    音乐整体能量强度。

    范围：
    0 - 1

    越高表示：
    节奏更活跃，
    情绪表达更强烈。
    """


    valence: float = Field(
        ge=0,
        le=1
    )
    """
    情绪积极程度。

    范围：
    0 - 1

    越高表示：
    情绪越积极、愉悦。
    """


    # =========================
    # 音乐属性
    # =========================

    tempo: int
    """
    音乐速度。

    单位：
    BPM
    """


    key: str
    """
    音乐调性。

    例如：
    C Major
    A Minor
    """


    instruments: list[str]
    """
    主要使用的乐器列表。

    例如：
    piano
    guitar
    strings
    """


    texture: str
    """
    音乐整体质感。

    例如：
    warm
    dreamy
    dark
    soft
    """


    # =========================
    # 场景信息
    # =========================

    scene: str
    """
    音乐对应的环境氛围。

    例如：
    late_night
    quiet_room
    sunny_afternoon
    """


    # =========================
    # 音乐发展趋势
    # =========================

    progression: Progression
    """
    音乐情绪的发展趋势。

    必须从 MuseGarden 定义的有限音乐发展标签中选择。
    """

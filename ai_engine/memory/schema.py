"""
用户音乐记忆数据结构

负责保存：
用户经历
    ↓
情绪理解结果
    ↓
Music Blueprint
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from ai_engine.blueprint.schema import MusicBlueprint


# 北京时间为 UTC+8，中国目前不使用夏令时。
BEIJING_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")


class EmotionSnapshot(BaseModel):
    """
    一次用户经历的情绪理解快照。
    """

    # 主要情绪
    primary_emotion: str = Field(min_length=1)

    # 伴随情绪
    secondary_emotions: list[str]

    # 发生场景
    scene: str = Field(min_length=1)

    @field_validator("primary_emotion", "scene")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        """拒绝只包含空格的情绪和场景字段。"""
        if not value.strip():
            raise ValueError("字段不能为空")
        return value


class MusicMemory(BaseModel):
    """
    一条完整的用户音乐记忆。

    保存用户原始输入、情绪理解结果和音乐设计结果。
    """

    # 记忆唯一标识，由系统自动生成
    id: UUID = Field(default_factory=uuid4)

    # 用户原始输入
    text: str = Field(min_length=1)

    # AI 对用户经历的情绪理解
    emotion: EmotionSnapshot

    # 对应的音乐设计结果
    blueprint: MusicBlueprint

    # 创建时间，统一使用北京时间
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        """保留原始输入，但拒绝只包含空格的内容。"""
        if not value.strip():
            raise ValueError("用户输入不能为空")
        return value

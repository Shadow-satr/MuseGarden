"""
用户创作草稿数据结构。

CreationDraft 用于保存尚未确认的当前创作结果。
它不同于已经确认并长期保存的 MusicMemory。
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory.schema import BEIJING_TIMEZONE, EmotionSnapshot


class CreationDraft(BaseModel):
    """
    一次尚未确认的音乐创作草稿。

    保存用户输入、当前情绪理解与候选 Music Blueprint。
    """

    # 草稿唯一标识，由系统自动生成
    id: UUID = Field(default_factory=uuid4)

    # 用户原始输入
    text: str = Field(min_length=1)

    # 当前情绪理解结果
    emotion: EmotionSnapshot

    # 当前候选音乐设计，不代表最终确认结果
    blueprint: MusicBlueprint

    # 草稿创建时间，统一使用北京时间
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        """拒绝只包含空格的用户原始输入。"""
        if not value.strip():
            raise ValueError("用户输入不能为空")
        return value


class BlueprintRevision(BaseModel):
    """
    一份 MusicBlueprint 的历史版本快照。

    用于记录同一份 CreationDraft 在某个时间点的完整音乐设计。
    """

    # 版本记录唯一标识，由系统自动生成
    id: UUID = Field(default_factory=uuid4)

    # 当前版本所属的创作草稿
    draft_id: UUID

    # 同一草稿内的版本顺序，初始版本从 1 开始
    version: int = Field(ge=1)

    # 初始版本没有修改指令，后续版本记录用户的修改要求
    edit_instruction: str | None = None

    # 保存完整 Blueprint 快照，而不是只保存变化字段
    blueprint: MusicBlueprint

    # 版本创建时间，统一使用北京时间
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @field_validator("edit_instruction")
    @classmethod
    def reject_blank_edit_instruction(cls, value: str | None) -> str | None:
        """允许初始版本没有指令，但拒绝只包含空格的指令。"""
        if value is not None and not value.strip():
            raise ValueError("修改要求不能为空白内容")
        return value

    @field_validator("blueprint")
    @classmethod
    def copy_blueprint_snapshot(cls, value: MusicBlueprint) -> MusicBlueprint:
        """复制完整 Blueprint，避免历史快照与外部对象共用引用。"""
        return MusicBlueprint.model_validate(value.model_dump())

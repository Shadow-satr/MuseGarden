"""Music Engine 内部使用的稳定生成输入、临时结果与音频资产契约。"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory.schema import BEIJING_TIMEZONE


class MusicGenerationSpec(BaseModel):
    """由 Blueprint Adapter 产出的、与具体 Provider 解耦的音乐生成规格。"""

    caption: str
    duration_seconds: int = Field(default=20, gt=0)
    bpm: int = Field(gt=0)
    key: str
    instrumental: bool = True
    seed: int | None = Field(default=None, ge=0)

    @field_validator("caption", "key")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        """拒绝无法供音乐模型或后续 Provider 使用的空文本。"""
        value = value.strip()
        if not value:
            raise ValueError("不能是空白字符串")
        return value


class AceStepGenerationResult(BaseModel):
    """ACE-Step Provider 返回的临时音频结果，不承担任何持久化职责。"""

    task_id: str
    audio_bytes: bytes = Field(min_length=1)
    content_type: str


class AudioArtifact(BaseModel):
    """一份已生成音频的元数据；真实音频由未来 Storage 步骤保存到 file_path。"""

    id: UUID = Field(default_factory=uuid4)
    draft_id: UUID
    revision_id: UUID
    generation_spec: MusicGenerationSpec
    provider: str = "ace_step"
    provider_task_id: str
    content_type: str
    file_path: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @field_validator("provider", "provider_task_id", "content_type", "file_path")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        """拒绝无法定位 Provider 任务或本地音频文件的空白字段。"""
        if not value.strip():
            raise ValueError("字段不能为空白内容")
        return value

    @field_validator("generation_spec")
    @classmethod
    def copy_generation_spec(cls, value: MusicGenerationSpec) -> MusicGenerationSpec:
        """保存独立的生成输入快照，避免后续修改外部对象影响历史资产。"""
        return MusicGenerationSpec.model_validate(value.model_dump())


class MusicConfirmationBundle(BaseModel):
    """最终确认前冻结的当前 Blueprint 与当前 AudioArtifact 快照。"""

    draft_id: UUID
    revision_id: UUID
    blueprint: MusicBlueprint
    audio_artifact: AudioArtifact

    @field_validator("blueprint")
    @classmethod
    def copy_blueprint_snapshot(cls, value: MusicBlueprint) -> MusicBlueprint:
        """确认包不与外部 Revision 共用 Blueprint 对象。"""
        return MusicBlueprint.model_validate(value.model_dump())

    @field_validator("audio_artifact")
    @classmethod
    def copy_audio_artifact_snapshot(cls, value: AudioArtifact) -> AudioArtifact:
        """确认包不与外部音频资产对象共用引用。"""
        return AudioArtifact.model_validate(value.model_dump())

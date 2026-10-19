"""用户已确认完成的 MuseGarden 创作成果及其本地 JSON 存储。"""

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory.schema import BEIJING_TIMEZONE
from music_engine.schema import AudioArtifact


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA_ROOT = PROJECT_ROOT / "database" / "local"


class FinalCreation(BaseModel):
    """用户最终确认的一次创作：冻结 Blueprint 与已选择的音乐资产。"""

    id: UUID = Field(default_factory=uuid4)
    draft_id: UUID
    revision_id: UUID
    memory_id: UUID
    audio_artifact_id: UUID
    blueprint: MusicBlueprint
    audio_artifact: AudioArtifact
    confirmed_at: datetime = Field(
        default_factory=lambda: datetime.now(BEIJING_TIMEZONE)
    )

    @field_validator("blueprint")
    @classmethod
    def copy_blueprint_snapshot(cls, value: MusicBlueprint) -> MusicBlueprint:
        return MusicBlueprint.model_validate(value.model_dump())

    @field_validator("audio_artifact")
    @classmethod
    def copy_audio_snapshot(cls, value: AudioArtifact) -> AudioArtifact:
        return AudioArtifact.model_validate(value.model_dump())

    @model_validator(mode="after")
    def validate_audio_relationship(self) -> "FinalCreation":
        """拒绝把其他 Draft / Revision 的音频写进最终成果。"""
        if self.audio_artifact_id != self.audio_artifact.id:
            raise ValueError("audio_artifact_id 必须与 audio_artifact.id 一致")
        if self.draft_id != self.audio_artifact.draft_id:
            raise ValueError("最终成果音频必须属于同一个 Draft")
        if self.revision_id != self.audio_artifact.revision_id:
            raise ValueError("最终成果音频必须属于同一个 BlueprintRevision")
        return self


class FinalCreationStore:
    """以 final_creations.json 保存最终成果；每个 Draft 只能归档一次。"""

    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = Path(data_root) if data_root else LOCAL_DATA_ROOT
        self.file_path = self.data_root / "final_creations.json"

    def save(self, final_creation: FinalCreation) -> None:
        """追加一份最终成果，并拒绝重复 ID 或重复 Draft 归档。"""
        creations = self.list_all()
        if any(item.id == final_creation.id for item in creations):
            raise ValueError(f"FinalCreation 已存在：{final_creation.id}")
        if any(item.draft_id == final_creation.draft_id for item in creations):
            raise ValueError(f"Draft 已完成最终归档：{final_creation.draft_id}")

        self._write_all([*creations, final_creation])

    def get(self, creation_id: UUID | str) -> FinalCreation | None:
        """按 FinalCreation ID 读取成果；不存在时返回 None。"""
        target_id = _normalize_uuid(creation_id)
        return next((item for item in self.list_all() if item.id == target_id), None)

    def get_by_draft(self, draft_id: UUID | str) -> FinalCreation | None:
        """读取某次 Draft 已有的最终成果，用于幂等确认。"""
        target_id = _normalize_uuid(draft_id)
        return next((item for item in self.list_all() if item.draft_id == target_id), None)

    def list_all(self) -> list[FinalCreation]:
        if not self.file_path.exists():
            return []

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f"最终成果 JSON 格式错误：{self.file_path}") from error

        if not isinstance(data, list):
            raise ValueError("最终成果最外层必须是 JSON 列表")

        try:
            return [FinalCreation.model_validate(item) for item in data]
        except ValidationError as error:
            raise ValueError("最终成果中存在无效数据") from error

    def _write_all(self, creations: list[FinalCreation]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self.file_path.with_name(f"{self.file_path.name}.tmp")
        data = [creation.model_dump(mode="json") for creation in creations]

        try:
            with temporary_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            temporary_file.replace(self.file_path)
        finally:
            temporary_file.unlink(missing_ok=True)


def _normalize_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError("UUID 格式无效。") from error

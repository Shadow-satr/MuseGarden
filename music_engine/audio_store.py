"""本地保存已生成的音频文件及其 AudioArtifact metadata。"""

import json
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError

from music_engine.schema import (
    AceStepGenerationResult,
    AudioArtifact,
    MusicGenerationSpec,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA_ROOT = PROJECT_ROOT / "database" / "local"


class AudioStore:
    """直接保存 WAV 与 JSON metadata，不负责调用音乐生成模型。"""

    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = Path(data_root) if data_root else LOCAL_DATA_ROOT
        self.audio_directory = self.data_root / "audio"
        self.metadata_file = self.data_root / "audio_artifacts.json"
        self.current_audio_file = self.data_root / "current_audio.json"

    def save(
        self,
        *,
        draft_id: UUID,
        revision_id: UUID,
        generation_spec: MusicGenerationSpec,
        generation_result: AceStepGenerationResult,
    ) -> AudioArtifact:
        """保存一条新音频；metadata 写入失败时会移除刚写入的 WAV。"""
        artifacts = self._load_artifacts()
        audio_id = uuid4()
        artifact = AudioArtifact(
            id=audio_id,
            draft_id=draft_id,
            revision_id=revision_id,
            generation_spec=generation_spec,
            provider_task_id=generation_result.task_id,
            content_type=generation_result.content_type,
            file_path=f"audio/{audio_id}.wav",
        )
        audio_path = self.data_root / artifact.file_path
        temporary_audio_path = audio_path.with_name(f"{audio_path.name}.tmp")

        self.audio_directory.mkdir(parents=True, exist_ok=True)
        if audio_path.exists():
            raise FileExistsError(f"音频文件已存在：{audio_path}")

        try:
            temporary_audio_path.write_bytes(generation_result.audio_bytes)
            temporary_audio_path.replace(audio_path)
            try:
                self._write_artifacts([*artifacts, artifact])
            except Exception:
                audio_path.unlink(missing_ok=True)
                raise
        finally:
            temporary_audio_path.unlink(missing_ok=True)

        return artifact

    def get(self, audio_id: UUID | str) -> AudioArtifact | None:
        """按资产 ID 读取 metadata；不存在时返回 None。"""
        target_id = _normalize_uuid(audio_id)
        return next(
            (artifact for artifact in self._load_artifacts() if artifact.id == target_id),
            None,
        )

    def list_by_revision(self, revision_id: UUID | str) -> list[AudioArtifact]:
        """按创建时间从旧到新返回某一 BlueprintRevision 的全部音频。"""
        target_id = _normalize_uuid(revision_id)
        artifacts = [
            artifact
            for artifact in self._load_artifacts()
            if artifact.revision_id == target_id
        ]
        return sorted(artifacts, key=lambda artifact: artifact.created_at)

    def list_by_draft(self, draft_id: UUID | str) -> list[AudioArtifact]:
        """按创建时间从旧到新返回某次创作的全部音频。"""
        target_id = _normalize_uuid(draft_id)
        artifacts = [
            artifact
            for artifact in self._load_artifacts()
            if artifact.draft_id == target_id
        ]
        return sorted(artifacts, key=lambda artifact: artifact.created_at)

    def get_latest_by_revision(self, revision_id: UUID | str) -> AudioArtifact | None:
        """返回某一 Revision 最新生成的音频；没有记录时返回 None。"""
        artifacts = self.list_by_revision(revision_id)
        return artifacts[-1] if artifacts else None

    def get_selected_audio_id(self, revision_id: UUID | str) -> UUID | None:
        """读取某一 Revision 的显式当前音频选择。"""
        return self._load_current_audio_selections().get(_normalize_uuid(revision_id))

    def set_selected_audio(self, revision_id: UUID | str, audio_id: UUID | str) -> None:
        """保存 Revision → AudioArtifact 的显式选择映射。"""
        selections = self._load_current_audio_selections()
        selections[_normalize_uuid(revision_id)] = _normalize_uuid(audio_id)
        self._write_current_audio_selections(selections)

    def clear_selected_audio(self, revision_id: UUID | str) -> None:
        """移除显式选择；不存在选择时保持安全。"""
        selections = self._load_current_audio_selections()
        target_id = _normalize_uuid(revision_id)
        if target_id in selections:
            del selections[target_id]
            self._write_current_audio_selections(selections)

    def load_audio(self, audio_id: UUID | str) -> bytes:
        """读取指定资产对应的真实音频字节。"""
        artifact = self.get(audio_id)
        if artifact is None:
            raise ValueError(f"音频资产不存在：{audio_id}")

        audio_path = self.data_root / artifact.file_path
        try:
            return audio_path.read_bytes()
        except FileNotFoundError as error:
            raise ValueError(f"音频文件不存在：{audio_path}") from error

    def _load_artifacts(self) -> list[AudioArtifact]:
        if not self.metadata_file.exists():
            return []

        try:
            with self.metadata_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f"音频 metadata JSON 格式错误：{self.metadata_file}") from error

        if not isinstance(data, list):
            raise ValueError("音频 metadata 最外层必须是 JSON 列表")

        try:
            return [AudioArtifact.model_validate(item) for item in data]
        except ValidationError as error:
            raise ValueError("音频 metadata 中存在无效数据") from error

    def _write_artifacts(self, artifacts: list[AudioArtifact]) -> None:
        """原子写入 metadata，避免中断破坏已有记录。"""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_metadata_file = self.metadata_file.with_name(
            f"{self.metadata_file.name}.tmp"
        )
        data = [artifact.model_dump(mode="json") for artifact in artifacts]

        try:
            with temporary_metadata_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            temporary_metadata_file.replace(self.metadata_file)
        finally:
            temporary_metadata_file.unlink(missing_ok=True)

    def _load_current_audio_selections(self) -> dict[UUID, UUID]:
        if not self.current_audio_file.exists():
            return {}

        try:
            with self.current_audio_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"当前音频选择 JSON 格式错误：{self.current_audio_file}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError("当前音频选择最外层必须是 JSON 对象")

        try:
            return {
                _normalize_uuid(revision_id): _normalize_uuid(audio_id)
                for revision_id, audio_id in data.items()
            }
        except ValueError as error:
            raise ValueError("当前音频选择中存在无效 UUID") from error

    def _write_current_audio_selections(self, selections: dict[UUID, UUID]) -> None:
        """原子写入轻量 Revision → AudioArtifact 选择映射。"""
        self.current_audio_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self.current_audio_file.with_name(
            f"{self.current_audio_file.name}.tmp"
        )
        data = {str(revision_id): str(audio_id) for revision_id, audio_id in selections.items()}

        try:
            with temporary_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            temporary_file.replace(self.current_audio_file)
        finally:
            temporary_file.unlink(missing_ok=True)


def _normalize_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError("UUID 格式无效。") from error

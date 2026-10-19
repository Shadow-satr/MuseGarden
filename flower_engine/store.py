"""FlowerArtifact 的最小本地 JSON 持久化。"""

import json
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from flower_engine.schema import FlowerArtifact


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA_ROOT = PROJECT_ROOT / "database" / "local"


class FlowerArtifactStore:
    """保存花朵资产快照，不负责生成、渲染或版本选择。"""

    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = Path(data_root) if data_root else LOCAL_DATA_ROOT
        self.file_path = self.data_root / "flower_artifacts.json"

    def save(self, artifact: FlowerArtifact) -> None:
        if not isinstance(artifact, FlowerArtifact):
            raise TypeError("artifact 必须是 FlowerArtifact 实例")

        artifacts = self.list_all()
        if any(item.id == artifact.id for item in artifacts):
            raise ValueError(f"FlowerArtifact 已存在：{artifact.id}")
        self._write_all([*artifacts, artifact])

    def get(self, artifact_id: UUID | str) -> FlowerArtifact | None:
        target_id = _normalize_uuid(artifact_id)
        return next(
            (artifact for artifact in self.list_all() if artifact.id == target_id),
            None,
        )

    def delete(self, artifact_id: UUID | str) -> FlowerArtifact:
        target_id = _normalize_uuid(artifact_id)
        artifacts = self.list_all()
        target = next((item for item in artifacts if item.id == target_id), None)
        if target is None:
            raise ValueError(f"FlowerArtifact 不存在：{target_id}")
        self._write_all([item for item in artifacts if item.id != target_id])
        return target

    def list_by_creation(
        self,
        creation_id: UUID | str,
    ) -> list[FlowerArtifact]:
        """按生成时间返回某次 FinalCreation 的完整花朵历史。"""
        target_id = _normalize_uuid(creation_id)
        artifacts = [
            artifact
            for artifact in self.list_all()
            if artifact.creation_id == target_id
        ]
        return sorted(artifacts, key=lambda artifact: artifact.created_at)

    def get_latest_by_creation(
        self,
        creation_id: UUID | str,
    ) -> FlowerArtifact | None:
        """返回某次 FinalCreation 最新生成的花；没有记录时返回 None。"""
        artifacts = self.list_by_creation(creation_id)
        return artifacts[-1] if artifacts else None

    def list_all(self) -> list[FlowerArtifact]:
        if not self.file_path.exists():
            return []

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"花朵资产 JSON 格式错误：{self.file_path}"
            ) from error

        if not isinstance(data, list):
            raise ValueError("花朵资产最外层必须是 JSON 列表")

        try:
            return [FlowerArtifact.model_validate(item) for item in data]
        except ValidationError as error:
            raise ValueError("花朵资产中存在无效数据") from error

    def _write_all(self, artifacts: list[FlowerArtifact]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self.file_path.with_name(f"{self.file_path.name}.tmp")
        data = [artifact.model_dump(mode="json") for artifact in artifacts]

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

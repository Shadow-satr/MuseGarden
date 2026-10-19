"""
音乐蓝图历史版本本地存储模块。

负责：
BlueprintRevision
    ↓
revisions.json
    ↓
程序重新启动后恢复 BlueprintRevision
"""

import json
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from .schema import BlueprintRevision


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 默认本地历史版本文件位置
REVISION_FILE = PROJECT_ROOT / "database" / "local" / "revisions.json"


def load_revisions(
    draft_id: UUID | str | None = None,
    file_path: Path | None = None,
) -> list[BlueprintRevision]:
    """
    读取历史 Blueprint 版本。

    不传 draft_id 时返回全部版本，保持文件中的保存顺序；
    传入 draft_id 时只返回对应草稿的版本，并按版本号从小到大排序。
    """
    revision_file = file_path or REVISION_FILE
    if not revision_file.exists():
        return []

    try:
        with revision_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"历史版本文件 JSON 格式错误：{revision_file}") from error

    if not isinstance(data, list):
        raise ValueError("历史版本文件最外层必须是 JSON 列表")

    try:
        revisions = [
            BlueprintRevision.model_validate(revision_data)
            for revision_data in data
        ]
    except ValidationError as error:
        raise ValueError("历史版本文件中存在无效数据") from error

    if draft_id is None:
        return revisions

    target_id = _normalize_draft_id(draft_id)
    matching_revisions = [
        revision
        for revision in revisions
        if revision.draft_id == target_id
    ]

    return sorted(matching_revisions, key=lambda revision: revision.version)


def save_revision(revision: BlueprintRevision, file_path: Path | None = None) -> None:
    """
    追加保存一条历史 Blueprint 版本。

    Revision ID 全局不能重复；同一 Draft 的版本号不能重复。
    """
    validated_revision = BlueprintRevision.model_validate(revision)
    revision_file = file_path or REVISION_FILE
    revisions = load_revisions(file_path=revision_file)

    if any(saved_revision.id == validated_revision.id for saved_revision in revisions):
        raise ValueError(f"历史版本已存在，不能重复保存：{validated_revision.id}")

    if any(
        saved_revision.draft_id == validated_revision.draft_id
        and saved_revision.version == validated_revision.version
        for saved_revision in revisions
    ):
        raise ValueError(
            "同一草稿不能保存重复版本号："
            f"{validated_revision.version}"
        )

    revisions.append(validated_revision)
    _write_revisions(revisions, revision_file)


def _write_revisions(revisions: list[BlueprintRevision], revision_file: Path | None = None) -> None:
    """安全写入完整历史版本列表，避免中断破坏旧文件。"""
    # 第一次保存时自动创建目录
    target_file = revision_file or REVISION_FILE
    target_file.parent.mkdir(parents=True, exist_ok=True)

    data = [revision.model_dump(mode="json") for revision in revisions]
    temporary_file = target_file.with_name(f"{target_file.name}.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    temporary_file.replace(target_file)


def _normalize_draft_id(draft_id: UUID | str) -> UUID:
    """将字符串或 UUID 统一转换为 UUID。"""
    if isinstance(draft_id, UUID):
        return draft_id

    try:
        return UUID(str(draft_id))
    except (TypeError, ValueError) as error:
        raise ValueError("草稿 ID 格式无效。") from error

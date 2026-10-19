"""
用户创作草稿本地存储模块。

负责：
CreationDraft
    ↓
drafts.json
    ↓
程序重新启动后恢复 CreationDraft
"""

import json
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from .schema import CreationDraft


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 默认本地草稿文件位置
DRAFT_FILE = PROJECT_ROOT / "database" / "local" / "drafts.json"


def load_drafts() -> list[CreationDraft]:
    """
    从本地 JSON 文件读取所有创作草稿。

    文件不存在时，说明还没有保存过草稿，返回空列表。
    """
    if not DRAFT_FILE.exists():
        return []

    try:
        with DRAFT_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"草稿文件 JSON 格式错误：{DRAFT_FILE}") from error

    if not isinstance(data, list):
        raise ValueError("草稿文件最外层必须是 JSON 列表")

    try:
        return [CreationDraft.model_validate(draft_data) for draft_data in data]
    except ValidationError as error:
        raise ValueError("草稿文件中存在无效数据") from error


def save_draft(draft: CreationDraft) -> None:
    """
    保存一条新的创作草稿。

    先写入临时文件，再替换正式文件，避免写入中断破坏已有草稿。
    """
    # 先读取已有草稿，保证不会覆盖旧数据
    drafts = load_drafts()

    # 同一个 id 只能保存一次
    if any(saved_draft.id == draft.id for saved_draft in drafts):
        raise ValueError(f"草稿已存在，不能重复保存：{draft.id}")

    drafts.append(draft)

    _write_drafts(drafts)


def delete_draft(draft_id: UUID | str) -> None:
    """删除指定 ID 的创作草稿，不影响其他草稿。"""
    target_id = _normalize_draft_id(draft_id)
    drafts = load_drafts()

    if not any(draft.id == target_id for draft in drafts):
        raise ValueError(f"草稿不存在，无法删除：{target_id}")

    remaining_drafts = [
        draft
        for draft in drafts
        if draft.id != target_id
    ]

    _write_drafts(remaining_drafts)


def replace_draft(draft: CreationDraft) -> None:
    """使用同 ID 的新草稿内容替换已保存草稿。"""
    drafts = load_drafts()

    if not any(saved_draft.id == draft.id for saved_draft in drafts):
        raise ValueError(f"草稿不存在，无法更新：{draft.id}")

    updated_drafts = [
        draft if saved_draft.id == draft.id else saved_draft
        for saved_draft in drafts
    ]

    _write_drafts(updated_drafts)


def _write_drafts(drafts: list[CreationDraft]) -> None:
    """安全写入完整草稿列表，避免中断破坏旧文件。"""
    # 第一次保存时自动创建目录
    DRAFT_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [draft.model_dump(mode="json") for draft in drafts]
    temporary_file = DRAFT_FILE.with_name(f"{DRAFT_FILE.name}.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    temporary_file.replace(DRAFT_FILE)


def _normalize_draft_id(draft_id: UUID | str) -> UUID:
    """将字符串或 UUID 统一转换为 UUID。"""
    if isinstance(draft_id, UUID):
        return draft_id

    try:
        return UUID(str(draft_id))
    except (TypeError, ValueError) as error:
        raise ValueError("草稿 ID 格式无效。") from error

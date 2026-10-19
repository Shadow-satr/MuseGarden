"""
用户创作草稿模块。
"""

from .schema import BlueprintRevision, CreationDraft
from .revision_store import load_revisions, save_revision
from .revision_compare import compare_blueprint_revisions
from .store import delete_draft, load_drafts, replace_draft, save_draft
from .manager import (
    confirm_draft,
    edit_creation_draft,
    restore_blueprint_revision,
    start_creation,
    update_draft_blueprint,
)

# 创作模块当前对外提供的草稿数据结构、存储和确认方法
__all__ = [
    "CreationDraft",
    "BlueprintRevision",
    "confirm_draft",
    "compare_blueprint_revisions",
    "delete_draft",
    "edit_creation_draft",
    "load_drafts",
    "load_revisions",
    "replace_draft",
    "restore_blueprint_revision",
    "save_draft",
    "save_revision",
    "start_creation",
    "update_draft_blueprint",
]

"""
音乐蓝图历史版本对比模块。

负责比较同一份 CreationDraft 的两个 BlueprintRevision，
只返回发生变化的 MusicBlueprint 字段。
"""

from copy import deepcopy
from typing import Any
from uuid import UUID

from ai_engine.blueprint.schema import MusicBlueprint

from .revision_store import load_revisions


def compare_blueprint_revisions(
    draft_id: UUID | str,
    version_a: int,
    version_b: int,
) -> dict[str, dict[str, Any]]:
    """
    比较同一草稿的两个历史 Blueprint 版本。

    返回格式：
    {
        "tempo": {"from": 85, "to": 95},
    }
    """
    target_id = _normalize_draft_id(draft_id)
    _validate_version(version_a, "version_a")
    _validate_version(version_b, "version_b")

    revisions = load_revisions(target_id)
    revision_a = next(
        (revision for revision in revisions if revision.version == version_a),
        None,
    )
    revision_b = next(
        (revision for revision in revisions if revision.version == version_b),
        None,
    )

    if revision_a is None:
        raise ValueError(f"历史版本不存在：V{version_a}")

    if revision_b is None:
        raise ValueError(f"历史版本不存在：V{version_b}")

    blueprint_a = revision_a.blueprint.model_dump(mode="json")
    blueprint_b = revision_b.blueprint.model_dump(mode="json")
    differences: dict[str, dict[str, Any]] = {}

    # 从 MusicBlueprint Schema 动态读取全部字段，避免手写字段列表。
    for field_name in MusicBlueprint.model_fields:
        value_a = blueprint_a[field_name]
        value_b = blueprint_b[field_name]

        if value_a != value_b:
            # 复制列表等可变值，避免调用方改动返回值影响历史数据。
            differences[field_name] = {
                "from": deepcopy(value_a),
                "to": deepcopy(value_b),
            }

    return differences


def _validate_version(version: int, name: str) -> None:
    """验证比较使用的版本号。"""
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError(f"{name} 必须是大于或等于 1 的整数。")


def _normalize_draft_id(draft_id: UUID | str) -> UUID:
    """将字符串或 UUID 统一转换为 UUID。"""
    if isinstance(draft_id, UUID):
        return draft_id

    try:
        return UUID(str(draft_id))
    except (TypeError, ValueError) as error:
        raise ValueError("草稿 ID 格式无效。") from error

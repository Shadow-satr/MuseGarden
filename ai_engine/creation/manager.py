"""
用户创作草稿确认服务。

负责将用户明确确认的 CreationDraft 提交为 MusicMemory，
并在长期记忆保存成功后移除对应草稿。
"""

from uuid import UUID

from ai_engine.blueprint.editor import edit_blueprint
from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory.manager import commit_memory
from ai_engine.memory.schema import MusicMemory
from ai_engine.memory.store import load_memories
from ai_engine.pipeline import run_creation_pipeline

from .revision_store import load_revisions, save_revision
from .schema import BlueprintRevision, CreationDraft
from .store import delete_draft, load_drafts, replace_draft, save_draft


def start_creation(
    text: str,
    use_memory: bool = True,
    top_k: int = 3,
) -> CreationDraft:
    """
    正式开始一次创作，并保存初始草稿和 Version 1。

    run_creation_pipeline() 只负责生成；
    本函数负责将生成结果正式暂存到本地。
    """
    draft = run_creation_pipeline(
        text=text,
        use_memory=use_memory,
        top_k=top_k,
    )

    # 先保存草稿，失败时不继续创建历史版本。
    save_draft(draft)

    initial_revision = BlueprintRevision(
        draft_id=draft.id,
        version=1,
        edit_instruction=None,
        blueprint=draft.blueprint,
    )

    try:
        save_revision(initial_revision)
    except Exception as revision_error:
        # 两个 JSON 文件没有事务：版本保存失败时，尝试删除本次新草稿。
        try:
            delete_draft(draft.id)
        except Exception as rollback_error:
            raise RuntimeError(
                "初始版本保存失败，且草稿回滚失败；草稿可能仍在本地。"
            ) from rollback_error

        raise revision_error

    return draft


def confirm_draft(draft_id: UUID | str) -> MusicMemory:
    """
    确认指定草稿，并将其提交为长期 MusicMemory。

    先保存 Memory，成功后才删除 Draft。
    """
    target_id = _normalize_draft_id(draft_id)
    drafts = load_drafts()
    draft = next(
        (saved_draft for saved_draft in drafts if saved_draft.id == target_id),
        None,
    )

    if draft is None:
        raise ValueError(f"草稿不存在，无法确认：{target_id}")

    existing_memory = _find_existing_memory(draft)

    # Memory 已保存但 Draft 删除失败时，重试只补做删除，不重复提交。
    if existing_memory is not None:
        delete_draft(draft.id)
        return existing_memory

    _validate_final_revision_consistency(draft)

    memory = commit_memory(
        text=draft.text,
        emotion=draft.emotion,
        blueprint=draft.blueprint,
        memory_id=draft.id,
    )

    # 只有 Memory 已成功保存或确认已存在时，才删除 Draft
    delete_draft(draft.id)

    return memory


def update_draft_blueprint(
    draft_id: UUID | str,
    blueprint: MusicBlueprint,
) -> CreationDraft:
    """
    使用新的 MusicBlueprint 更新指定草稿的当前候选设计。

    只替换 blueprint，保留 Draft 的其他字段不变。
    """
    target_id = _normalize_draft_id(draft_id)
    validated_blueprint = MusicBlueprint.model_validate(blueprint)
    drafts = load_drafts()
    draft = next(
        (saved_draft for saved_draft in drafts if saved_draft.id == target_id),
        None,
    )

    if draft is None:
        raise ValueError(f"草稿不存在，无法更新：{target_id}")

    if any(memory.id == draft.id for memory in load_memories()):
        raise ValueError("已确认并存在长期 Memory 的草稿不能继续修改。")

    updated_draft = CreationDraft(
        id=draft.id,
        text=draft.text,
        emotion=draft.emotion,
        blueprint=validated_blueprint,
        created_at=draft.created_at,
    )

    replace_draft(updated_draft)

    return updated_draft


def edit_creation_draft(
    draft_id: UUID | str,
    edit_instruction: str,
) -> CreationDraft:
    """
    根据用户自然语言修改要求，更新指定创作草稿。

    先让 AI 生成并校验新的 Blueprint，
    成功后才写回原来的 Draft。
    """
    target_id = _normalize_draft_id(draft_id)

    if not isinstance(edit_instruction, str) or not edit_instruction.strip():
        raise ValueError("用户修改要求不能为空。")

    drafts = load_drafts()
    draft = next(
        (saved_draft for saved_draft in drafts if saved_draft.id == target_id),
        None,
    )

    if draft is None:
        raise ValueError(f"草稿不存在，无法修改：{target_id}")

    # 如果确认时 Memory 已保存、但 Draft 删除失败，也不能继续修改。
    if any(memory.id == draft.id for memory in load_memories()):
        raise ValueError("已确认并存在长期 Memory 的草稿不能继续修改。")

    revision_history = load_revisions(draft.id)

    if revision_history:
        if not any(revision.blueprint == draft.blueprint for revision in revision_history):
            raise ValueError("当前草稿不属于任何历史版本，无法继续修改。")
        next_version = max(revision.version for revision in revision_history) + 1
    else:
        # 兼容 Step 12.7 之前手动保存的旧草稿。
        # 必须先保存初始版本，失败时不调用 AI 编辑器。
        initial_revision = BlueprintRevision(
            draft_id=draft.id,
            version=1,
            edit_instruction=None,
            blueprint=draft.blueprint,
        )
        save_revision(initial_revision)
        next_version = 2

    # 保存一份修改前快照，用于 Revision 保存失败时回滚。
    previous_blueprint = MusicBlueprint.model_validate(draft.blueprint.model_dump())

    # 编辑失败时异常会直接暴露，下面的草稿更新不会执行。
    new_blueprint = edit_blueprint(
        original_text=draft.text,
        current_blueprint=draft.blueprint,
        edit_instruction=edit_instruction,
    )

    updated_draft = update_draft_blueprint(draft.id, new_blueprint)
    new_revision = BlueprintRevision(
        draft_id=draft.id,
        version=next_version,
        edit_instruction=edit_instruction,
        blueprint=new_blueprint,
    )

    try:
        save_revision(new_revision)
    except Exception as revision_error:
        _rollback_draft_blueprint(
            draft_id=draft.id,
            expected_blueprint=new_blueprint,
            previous_blueprint=previous_blueprint,
        )
        raise revision_error

    return updated_draft


def restore_blueprint_revision(
    draft_id: UUID | str,
    target_version: int,
) -> CreationDraft:
    """
    将指定历史版本恢复为当前草稿 Blueprint。

    恢复只切换当前草稿到既有版本，不删除或复制任何历史记录。
    """
    target_id = _normalize_draft_id(draft_id)

    if (
        not isinstance(target_version, int)
        or isinstance(target_version, bool)
        or target_version < 1
    ):
        raise ValueError("目标版本号必须是大于或等于 1 的整数。")

    drafts = load_drafts()
    draft = next(
        (saved_draft for saved_draft in drafts if saved_draft.id == target_id),
        None,
    )

    if draft is None:
        raise ValueError(f"草稿不存在，无法恢复版本：{target_id}")

    if any(memory.id == draft.id for memory in load_memories()):
        raise ValueError("已确认并存在长期 Memory 的草稿不能恢复版本。")

    revision_history = load_revisions(draft.id)

    if not revision_history:
        raise ValueError("草稿没有可恢复的历史版本。")

    target_revision = next(
        (
            revision
            for revision in revision_history
            if revision.version == target_version
        ),
        None,
    )

    if target_revision is None:
        raise ValueError(f"目标历史版本不存在：V{target_version}")

    # 当前已经是目标版本时，不重复创建相同的恢复版本。
    if draft.blueprint == target_revision.blueprint:
        return draft

    restored_blueprint = MusicBlueprint.model_validate(
        target_revision.blueprint.model_dump()
    )
    # 恢复是切换到已有版本，不复制 Blueprint，也不创建重复 Revision。
    return update_draft_blueprint(draft.id, restored_blueprint)


def _rollback_draft_blueprint(
    draft_id: UUID,
    expected_blueprint: MusicBlueprint,
    previous_blueprint: MusicBlueprint,
) -> None:
    """仅在草稿仍是本次新 Blueprint 时，尝试恢复修改前的 Blueprint。"""
    try:
        current_draft = next(
            (draft for draft in load_drafts() if draft.id == draft_id),
            None,
        )

        if current_draft is None or current_draft.blueprint != expected_blueprint:
            raise RuntimeError("草稿当前状态已变化，无法安全回滚。")

        update_draft_blueprint(draft_id, previous_blueprint)
    except Exception as rollback_error:
        raise RuntimeError(
            "新历史版本保存失败，且草稿回滚失败；数据可能不一致。"
        ) from rollback_error


def _find_existing_memory(draft: CreationDraft) -> MusicMemory | None:
    """查找同 Draft UUID 的 Memory，并检查内容是否一致。"""
    existing_memory = next(
        (memory for memory in load_memories() if memory.id == draft.id),
        None,
    )

    if existing_memory is None:
        return None

    if (
        existing_memory.text != draft.text
        or existing_memory.emotion != draft.emotion
        or existing_memory.blueprint != draft.blueprint
    ):
        raise ValueError("草稿 ID 已存在内容冲突的长期 Memory。")

    return existing_memory


def _validate_final_revision_consistency(draft: CreationDraft) -> None:
    """确认前检查当前 Draft 是否对应某个历史版本。"""
    revision_history = load_revisions(draft.id)

    # 兼容版本系统出现前保存的旧 Draft。
    if not revision_history:
        return

    if not any(revision.blueprint == draft.blueprint for revision in revision_history):
        raise ValueError("当前草稿不属于任何历史版本，无法确认。")


def _normalize_draft_id(draft_id: UUID | str) -> UUID:
    """将字符串或 UUID 统一转换为 UUID。"""
    if isinstance(draft_id, UUID):
        return draft_id

    try:
        return UUID(str(draft_id))
    except (TypeError, ValueError) as error:
        raise ValueError("草稿 ID 格式无效。") from error

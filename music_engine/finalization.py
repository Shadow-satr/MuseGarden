"""编排 Music 确认准备、AI Engine Draft 确认与 FinalCreation 归档。"""

from collections.abc import Callable
from uuid import UUID

from ai_engine.creation import CreationDraft, confirm_draft, load_drafts, save_draft
from ai_engine.memory.schema import MusicMemory
from music_engine.final_creation import FinalCreation, FinalCreationStore
from music_engine.workspace import MusicWorkspaceService


class CreationFinalizationService:
    """以 prepare → confirm → archive 的顺序完成一次跨 Engine 最终确认。"""

    def __init__(
        self,
        workspace: MusicWorkspaceService,
        final_store: FinalCreationStore,
        confirm_draft_fn: Callable[[UUID | str], MusicMemory] = confirm_draft,
        load_drafts_fn: Callable[[], list[CreationDraft]] = load_drafts,
        save_draft_fn: Callable[[CreationDraft], None] = save_draft,
    ) -> None:
        self.workspace = workspace
        self.final_store = final_store
        self.confirm_draft = confirm_draft_fn
        self.load_drafts = load_drafts_fn
        self.save_draft = save_draft_fn

    def finalize(self, draft_id: UUID | str) -> FinalCreation:
        """准备音乐、确认 Draft，并将最终成果归档；重复调用返回已有成果。"""
        target_id = _normalize_draft_id(draft_id)
        existing = self.final_store.get_by_draft(target_id)
        if existing is not None:
            return existing

        draft = self._load_draft(target_id)
        bundle = self.workspace.prepare_confirmation(target_id)
        memory = self.confirm_draft(target_id)
        if memory.id != bundle.draft_id:
            self._restore_draft(draft)
            raise RuntimeError("confirm_draft() 返回的 MusicMemory ID 与 Draft 不一致。")

        final_creation = FinalCreation(
            draft_id=bundle.draft_id,
            revision_id=bundle.revision_id,
            memory_id=memory.id,
            audio_artifact_id=bundle.audio_artifact.id,
            blueprint=bundle.blueprint,
            audio_artifact=bundle.audio_artifact,
        )
        try:
            self.final_store.save(final_creation)
        except Exception:
            self._restore_draft(draft)
            raise
        return final_creation

    def _load_draft(self, draft_id: UUID) -> CreationDraft:
        draft = next(
            (saved_draft for saved_draft in self.load_drafts() if saved_draft.id == draft_id),
            None,
        )
        if draft is None:
            raise ValueError(f"草稿不存在，无法最终确认：{draft_id}")
        return draft

    def _restore_draft(self, draft: CreationDraft) -> None:
        """归档后续步骤失败时恢复 Draft，使用户可以安全重试最终确认。"""
        try:
            self.save_draft(draft)
        except Exception as restore_error:
            raise RuntimeError(
                "最终成果归档失败，且草稿恢复失败；需要人工检查确认状态。"
            ) from restore_error


def _normalize_draft_id(draft_id: UUID | str) -> UUID:
    if isinstance(draft_id, UUID):
        return draft_id

    try:
        return UUID(str(draft_id))
    except (TypeError, ValueError) as error:
        raise ValueError("草稿 ID 格式无效。") from error

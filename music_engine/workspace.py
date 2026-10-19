"""将 Draft 当前 BlueprintRevision 与 Music Engine 服务连接起来。"""

from collections.abc import Callable
from uuid import UUID

from ai_engine.creation import BlueprintRevision, CreationDraft, load_drafts, load_revisions
from music_engine.schema import AudioArtifact, MusicConfirmationBundle
from music_engine.service import MusicGenerationService
from music_engine.version_service import MusicVersionService


class MusicWorkspaceService:
    """让上层只凭 Draft ID 操作当前 Revision 对应的音乐。"""

    def __init__(
        self,
        generation_service: MusicGenerationService,
        version_service: MusicVersionService,
        load_drafts_fn: Callable[[], list[CreationDraft]] = load_drafts,
        load_revisions_fn: Callable[[UUID | str | None], list[BlueprintRevision]] = load_revisions,
    ) -> None:
        self.generation_service = generation_service
        self.version_service = version_service
        self.load_drafts = load_drafts_fn
        self.load_revisions = load_revisions_fn

    def generate_current(
        self,
        draft_id: UUID | str,
        duration_seconds: int = 20,
        seed: int | None = None,
    ) -> AudioArtifact:
        """为 Draft 当前 Revision 生成并保存一份新音频。"""
        draft, revision = self._get_current_revision(draft_id)
        return self.generation_service.generate_for_revision(
            draft_id=draft.id,
            revision=revision,
            duration_seconds=duration_seconds,
            seed=seed,
        )

    def list_current_revision_audio(self, draft_id: UUID | str) -> list[AudioArtifact]:
        """返回 Draft 当前 Revision 的全部候选音频。"""
        _, revision = self._get_current_revision(draft_id)
        return self.version_service.list_for_revision(revision.id)

    def get_current_audio(self, draft_id: UUID | str) -> AudioArtifact | None:
        """返回 Draft 当前 Revision 应播放的音频；未生成时返回 None。"""
        _, revision = self._get_current_revision(draft_id)
        return self.version_service.get_current_for_revision(revision.id)

    def select_audio(
        self,
        draft_id: UUID | str,
        audio_id: UUID | str,
    ) -> AudioArtifact:
        """选择 Draft 当前 Revision 的某份候选音频。"""
        _, revision = self._get_current_revision(draft_id)
        return self.version_service.select_current(revision.id, audio_id)

    def clear_audio_selection(self, draft_id: UUID | str) -> None:
        """取消 Draft 当前 Revision 的显式音频选择。"""
        _, revision = self._get_current_revision(draft_id)
        self.version_service.clear_current_selection(revision.id)

    def prepare_confirmation(
        self,
        draft_id: UUID | str,
    ) -> MusicConfirmationBundle:
        """冻结 Draft 当前 Revision 及其当前音频，供未来最终确认流程交接。"""
        draft, revision = self._get_current_revision(draft_id)
        audio_artifact = self.version_service.get_current_for_revision(revision.id)
        if audio_artifact is None:
            raise ValueError("当前 BlueprintRevision 尚未生成音乐，无法准备确认。")

        if audio_artifact.draft_id != draft.id:
            raise ValueError("当前音频不属于该 CreationDraft，无法准备确认。")
        if audio_artifact.revision_id != revision.id:
            raise ValueError("当前音频不属于当前 BlueprintRevision，无法准备确认。")

        return MusicConfirmationBundle(
            draft_id=draft.id,
            revision_id=revision.id,
            blueprint=revision.blueprint,
            audio_artifact=audio_artifact,
        )

    def _get_current_revision(
        self,
        draft_id: UUID | str,
    ) -> tuple[CreationDraft, BlueprintRevision]:
        target_id = _normalize_draft_id(draft_id)
        draft = next(
            (saved_draft for saved_draft in self.load_drafts() if saved_draft.id == target_id),
            None,
        )
        if draft is None:
            raise ValueError(f"草稿不存在：{target_id}")

        revisions = self.load_revisions(draft.id)
        if not revisions:
            raise ValueError("草稿没有可用的 BlueprintRevision。")

        current_revision = next(
            (revision for revision in reversed(revisions) if revision.blueprint == draft.blueprint),
            None,
        )
        if current_revision is None:
            raise ValueError("当前草稿不属于任何 BlueprintRevision。")
        return draft, current_revision


def _normalize_draft_id(draft_id: UUID | str) -> UUID:
    if isinstance(draft_id, UUID):
        return draft_id

    try:
        return UUID(str(draft_id))
    except (TypeError, ValueError) as error:
        raise ValueError("草稿 ID 格式无效。") from error

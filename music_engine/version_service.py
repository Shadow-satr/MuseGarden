"""查询 AudioArtifact 历史，并给出当前默认音频。"""

from uuid import UUID

from music_engine.audio_store import AudioStore
from music_engine.schema import AudioArtifact


class MusicVersionService:
    """默认使用最新音频；用户也可显式固定某份历史音频。"""

    def __init__(self, audio_store: AudioStore) -> None:
        self.audio_store = audio_store

    def list_for_revision(self, revision_id: UUID | str) -> list[AudioArtifact]:
        """返回一份 Revision 的全部音频历史。"""
        return self.audio_store.list_by_revision(revision_id)

    def list_for_draft(self, draft_id: UUID | str) -> list[AudioArtifact]:
        """返回一份 Draft 的全部音频历史。"""
        return self.audio_store.list_by_draft(draft_id)

    def get_current_for_revision(self, revision_id: UUID | str) -> AudioArtifact | None:
        """优先返回显式选择；没有选择时才使用最新 Artifact。"""
        selected_audio_id = self.audio_store.get_selected_audio_id(revision_id)
        if selected_audio_id is None:
            return self.audio_store.get_latest_by_revision(revision_id)

        artifact = self.audio_store.get(selected_audio_id)
        if artifact is None:
            raise RuntimeError("当前音频选择引用了不存在的 AudioArtifact")

        if artifact.revision_id != _normalize_uuid(revision_id):
            raise RuntimeError("当前音频选择的 AudioArtifact 不属于该 BlueprintRevision")
        return artifact

    def select_current(
        self,
        revision_id: UUID | str,
        audio_id: UUID | str,
    ) -> AudioArtifact:
        """显式固定同一 Revision 的一份历史音频作为当前版本。"""
        artifact = self.audio_store.get(audio_id)
        if artifact is None:
            raise ValueError(f"音频资产不存在：{audio_id}")

        if artifact.revision_id != _normalize_uuid(revision_id):
            raise ValueError("不能选择属于其他 BlueprintRevision 的音频")

        self.audio_store.set_selected_audio(revision_id, artifact.id)
        return artifact

    def clear_current_selection(self, revision_id: UUID | str) -> None:
        """取消显式固定，恢复“最新音频为当前”的自动规则。"""
        self.audio_store.clear_selected_audio(revision_id)

def _normalize_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError("Revision ID 格式无效。") from error

"""编排 Blueprint 适配、ACE-Step 生成与音频持久化。"""

from uuid import UUID

from ai_engine.creation.schema import BlueprintRevision
from music_engine.adapter import blueprint_to_generation_spec
from music_engine.audio_store import AudioStore
from music_engine.providers.ace_step import AceStepClient
from music_engine.schema import AudioArtifact


class MusicGenerationService:
    """为一份 BlueprintRevision 生成并保存一份新的音乐资产。"""

    def __init__(self, client: AceStepClient, audio_store: AudioStore) -> None:
        self.client = client
        self.audio_store = audio_store

    def generate_for_revision(
        self,
        *,
        draft_id: UUID,
        revision: BlueprintRevision,
        duration_seconds: int = 20,
        seed: int | None = None,
    ) -> AudioArtifact:
        """按 Revision 的 Blueprint 生成一份新 AudioArtifact。"""
        spec = blueprint_to_generation_spec(
            revision.blueprint,
            duration_seconds=duration_seconds,
            seed=seed,
        )
        result = self.client.generate_audio(spec)
        return self.audio_store.save(
            draft_id=draft_id,
            revision_id=revision.id,
            generation_spec=spec,
            generation_result=result,
        )

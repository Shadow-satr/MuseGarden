"""Step 13.10：最终确认前的 MusicConfirmationBundle 测试。"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import BlueprintRevision, CreationDraft
from ai_engine.memory.schema import EmotionSnapshot
from music_engine import (
    AudioArtifact,
    MusicConfirmationBundle,
    MusicGenerationService,
    MusicGenerationSpec,
    MusicVersionService,
)
from music_engine.workspace import MusicWorkspaceService


def _blueprint(tempo: int = 92) -> MusicBlueprint:
    return MusicBlueprint(
        primary_emotion="满足感",
        secondary_emotions=["疲劳"],
        energy=0.55,
        valence=0.8,
        tempo=tempo,
        key="C Major",
        instruments=["piano", "strings"],
        texture="warm",
        scene="比赛结束之后",
        progression="calm_to_rising",
    )


def _workspace(draft: CreationDraft, revisions: list[BlueprintRevision]):
    generation = MagicMock(spec=MusicGenerationService)
    versions = MagicMock(spec=MusicVersionService)
    workspace = MusicWorkspaceService(
        generation,
        versions,
        load_drafts_fn=lambda: [draft],
        load_revisions_fn=lambda _draft_id: revisions,
    )
    return workspace, generation, versions


def _artifact(draft_id, revision_id, task_id="ace-task-001") -> AudioArtifact:
    return AudioArtifact(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=MusicGenerationSpec(
            caption="Warm instrumental music.", bpm=92, key="C Major"
        ),
        provider_task_id=task_id,
        content_type="audio/wav",
        file_path=f"audio/{task_id}.wav",
    )


def test_prepare_confirmation_uses_current_pinned_audio_and_creates_snapshot():
    draft_id = uuid4()
    blueprint = _blueprint()
    draft = CreationDraft(
        id=draft_id,
        text="比赛结束后很满足。",
        emotion=EmotionSnapshot(
            primary_emotion="满足感", secondary_emotions=["疲劳"], scene="比赛结束之后"
        ),
        blueprint=blueprint,
    )
    revision = BlueprintRevision(draft_id=draft_id, version=3, blueprint=blueprint)
    workspace, generation, versions = _workspace(draft, [revision])
    latest_audio = _artifact(draft_id, revision.id, "ace-task-latest")
    pinned_audio = _artifact(draft_id, revision.id, "ace-task-pinned")
    versions.get_current_for_revision.return_value = pinned_audio
    original_revision = revision.model_dump(mode="json")

    bundle = workspace.prepare_confirmation(draft_id)

    assert isinstance(bundle, MusicConfirmationBundle)
    assert bundle.draft_id == draft_id
    assert bundle.revision_id == revision.id
    assert bundle.blueprint == revision.blueprint
    assert bundle.audio_artifact == pinned_audio
    assert bundle.audio_artifact != latest_audio
    versions.get_current_for_revision.assert_called_once_with(revision.id)
    generation.generate_for_revision.assert_not_called()
    assert revision.model_dump(mode="json") == original_revision

    revision.blueprint.tempo = 70
    pinned_audio.generation_spec.caption = "Changed after confirmation."
    assert bundle.blueprint.tempo == 92
    assert bundle.audio_artifact.generation_spec.caption == "Warm instrumental music."


def test_prepare_confirmation_rejects_no_current_audio_or_mismatched_audio():
    draft_id = uuid4()
    blueprint = _blueprint()
    draft = CreationDraft(
        id=draft_id,
        text="比赛结束后很满足。",
        emotion=EmotionSnapshot(
            primary_emotion="满足感", secondary_emotions=["疲劳"], scene="比赛结束之后"
        ),
        blueprint=blueprint,
    )
    current_revision = BlueprintRevision(draft_id=draft_id, version=3, blueprint=blueprint)
    workspace, _, versions = _workspace(draft, [current_revision])

    versions.get_current_for_revision.return_value = None
    with pytest.raises(ValueError, match="尚未生成音乐"):
        workspace.prepare_confirmation(draft_id)

    versions.get_current_for_revision.return_value = _artifact(uuid4(), current_revision.id)
    with pytest.raises(ValueError, match="CreationDraft"):
        workspace.prepare_confirmation(draft_id)

    versions.get_current_for_revision.return_value = _artifact(draft_id, uuid4())
    with pytest.raises(ValueError, match="当前 BlueprintRevision"):
        workspace.prepare_confirmation(draft_id)


def test_new_or_restored_revision_without_audio_cannot_confirm():
    draft_id = uuid4()
    original_revision = BlueprintRevision(draft_id=draft_id, version=1, blueprint=_blueprint(92))
    restored_revision = BlueprintRevision(
        draft_id=draft_id,
        version=4,
        blueprint=original_revision.blueprint,
    )
    draft = CreationDraft(
        id=draft_id,
        text="恢复后准备确认。",
        emotion=EmotionSnapshot(primary_emotion="平静", secondary_emotions=[], scene="恢复"),
        blueprint=restored_revision.blueprint,
    )
    workspace, _, versions = _workspace(draft, [original_revision, restored_revision])
    versions.get_current_for_revision.return_value = None

    with pytest.raises(ValueError, match="尚未生成音乐"):
        workspace.prepare_confirmation(draft_id)
    versions.get_current_for_revision.assert_called_once_with(restored_revision.id)

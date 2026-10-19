"""Step 13.9：Draft-aware Music Workspace 测试，不调用真实模型或文件存储。"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import BlueprintRevision, CreationDraft
from ai_engine.memory.schema import EmotionSnapshot
from music_engine import AudioArtifact, MusicGenerationService, MusicVersionService
from music_engine.schema import MusicGenerationSpec
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


def _draft(draft_id, blueprint: MusicBlueprint) -> CreationDraft:
    return CreationDraft(
        id=draft_id,
        text="比赛结束后很满足。",
        emotion=EmotionSnapshot(
            primary_emotion="满足感",
            secondary_emotions=["疲劳"],
            scene="比赛结束之后",
        ),
        blueprint=blueprint,
    )


def _artifact(draft_id, revision_id) -> AudioArtifact:
    return AudioArtifact(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=MusicGenerationSpec(
            caption="Warm instrumental music.", bpm=92, key="C Major"
        ),
        provider_task_id="ace-task-001",
        content_type="audio/wav",
        file_path="audio/example.wav",
    )


def _workspace(draft, revisions):
    generation = MagicMock(spec=MusicGenerationService)
    versions = MagicMock(spec=MusicVersionService)
    workspace = MusicWorkspaceService(
        generation,
        versions,
        load_drafts_fn=lambda: [draft],
        load_revisions_fn=lambda _draft_id: revisions,
    )
    return workspace, generation, versions


def test_workspace_delegates_all_current_revision_operations():
    draft_id = uuid4()
    revision = BlueprintRevision(draft_id=draft_id, version=1, blueprint=_blueprint())
    draft = _draft(draft_id, revision.blueprint)
    workspace, generation, versions = _workspace(draft, [revision])
    artifact = _artifact(draft_id, revision.id)
    generation.generate_for_revision.return_value = artifact
    versions.list_for_revision.return_value = [artifact]
    versions.get_current_for_revision.return_value = artifact
    versions.select_current.return_value = artifact
    original_blueprint = revision.blueprint.model_dump(mode="json")

    assert workspace.generate_current(draft_id, duration_seconds=30, seed=20261006) == artifact
    generation.generate_for_revision.assert_called_once_with(
        draft_id=draft_id,
        revision=revision,
        duration_seconds=30,
        seed=20261006,
    )
    assert workspace.list_current_revision_audio(draft_id) == [artifact]
    assert workspace.get_current_audio(draft_id) == artifact
    assert workspace.select_audio(draft_id, artifact.id) == artifact
    workspace.clear_audio_selection(draft_id)
    versions.list_for_revision.assert_called_once_with(revision.id)
    versions.get_current_for_revision.assert_called_once_with(revision.id)
    versions.select_current.assert_called_once_with(revision.id, artifact.id)
    versions.clear_current_selection.assert_called_once_with(revision.id)
    assert revision.blueprint.model_dump(mode="json") == original_blueprint


def test_workspace_uses_new_revision_without_reusing_old_audio():
    draft_id = uuid4()
    old_revision = BlueprintRevision(draft_id=draft_id, version=1, blueprint=_blueprint(92))
    current_revision = BlueprintRevision(draft_id=draft_id, version=2, blueprint=_blueprint(80))
    draft = _draft(draft_id, current_revision.blueprint)
    workspace, _, versions = _workspace(draft, [old_revision, current_revision])
    old_audio = _artifact(draft_id, old_revision.id)
    versions.get_current_for_revision.return_value = None

    assert workspace.get_current_audio(draft_id) is None
    versions.get_current_for_revision.assert_called_once_with(current_revision.id)
    assert old_audio.revision_id != current_revision.id

    versions.select_current.side_effect = ValueError("不能选择属于其他 BlueprintRevision 的音频")
    with pytest.raises(ValueError, match="其他"):
        workspace.select_audio(draft_id, old_audio.id)
    versions.select_current.assert_called_once_with(current_revision.id, old_audio.id)


def test_workspace_restore_uses_the_original_revision_audio():
    draft_id = uuid4()
    original_revision = BlueprintRevision(draft_id=draft_id, version=1, blueprint=_blueprint(92))
    changed_revision = BlueprintRevision(draft_id=draft_id, version=2, blueprint=_blueprint(80))
    draft = _draft(draft_id, original_revision.blueprint)
    workspace, _, versions = _workspace(
        draft,
        [original_revision, changed_revision],
    )
    versions.get_current_for_revision.return_value = None

    assert workspace.get_current_audio(draft_id) is None
    versions.get_current_for_revision.assert_called_once_with(original_revision.id)


def test_workspace_rejects_missing_draft_or_invalid_current_revision():
    existing_draft_id = uuid4()
    draft = _draft(existing_draft_id, _blueprint())
    workspace, _, _ = _workspace(draft, [])

    with pytest.raises(ValueError, match="草稿不存在"):
        workspace.get_current_audio(uuid4())
    with pytest.raises(ValueError, match="没有可用"):
        workspace.get_current_audio(existing_draft_id)

    inconsistent_revision = BlueprintRevision(
        draft_id=existing_draft_id,
        version=1,
        blueprint=_blueprint(80),
    )
    inconsistent_workspace, _, _ = _workspace(draft, [inconsistent_revision])
    with pytest.raises(ValueError, match="任何"):
        inconsistent_workspace.get_current_audio(existing_draft_id)

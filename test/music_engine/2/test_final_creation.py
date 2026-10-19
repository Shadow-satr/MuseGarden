"""Step 13.11：跨 Engine 最终确认与 FinalCreation 归档测试。"""

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import CreationDraft
from ai_engine.memory.schema import EmotionSnapshot, MusicMemory
from music_engine import (
    AudioArtifact,
    CreationFinalizationService,
    FinalCreationStore,
    MusicConfirmationBundle,
    MusicGenerationSpec,
)


def _draft(draft_id) -> CreationDraft:
    blueprint = MusicBlueprint(
        primary_emotion="满足感",
        secondary_emotions=["疲劳"],
        energy=0.55,
        valence=0.8,
        tempo=92,
        key="C Major",
        instruments=["piano", "strings"],
        texture="warm",
        scene="比赛结束之后",
        progression="calm_to_rising",
    )
    return CreationDraft(
        id=draft_id,
        text="比赛结束后很满足。",
        emotion=EmotionSnapshot(
            primary_emotion="满足感", secondary_emotions=["疲劳"], scene="比赛结束之后"
        ),
        blueprint=blueprint,
    )


def _bundle(draft: CreationDraft) -> MusicConfirmationBundle:
    revision_id = uuid4()
    audio = AudioArtifact(
        draft_id=draft.id,
        revision_id=revision_id,
        generation_spec=MusicGenerationSpec(
            caption="Warm instrumental music.", bpm=92, key="C Major"
        ),
        provider_task_id="ace-task-pinned",
        content_type="audio/wav",
        file_path="audio/pinned.wav",
    )
    return MusicConfirmationBundle(
        draft_id=draft.id,
        revision_id=revision_id,
        blueprint=draft.blueprint,
        audio_artifact=audio,
    )


def _service(tmp_path, draft, bundle):
    workspace = MagicMock()
    workspace.prepare_confirmation.return_value = bundle
    confirm = MagicMock(
        return_value=MusicMemory(
            id=draft.id,
            text=draft.text,
            emotion=draft.emotion,
            blueprint=draft.blueprint,
        )
    )
    restored_drafts = []
    service = CreationFinalizationService(
        workspace,
        FinalCreationStore(tmp_path),
        confirm_draft_fn=confirm,
        load_drafts_fn=lambda: [draft],
        save_draft_fn=restored_drafts.append,
    )
    return service, workspace, confirm, restored_drafts


def test_finalize_archives_confirmation_and_is_idempotent(tmp_path):
    draft = _draft(uuid4())
    bundle = _bundle(draft)
    service, workspace, confirm, restored_drafts = _service(tmp_path, draft, bundle)

    final = service.finalize(draft.id)

    assert final.draft_id == draft.id
    assert final.revision_id == bundle.revision_id
    assert final.memory_id == draft.id
    assert final.audio_artifact_id == bundle.audio_artifact.id
    assert final.blueprint == bundle.blueprint
    assert final.audio_artifact == bundle.audio_artifact
    workspace.prepare_confirmation.assert_called_once_with(draft.id)
    confirm.assert_called_once_with(draft.id)
    assert restored_drafts == []

    data = json.loads((tmp_path / "final_creations.json").read_text(encoding="utf-8"))
    assert data == [final.model_dump(mode="json")]
    assert service.final_store.get(final.id) == final
    assert service.final_store.get_by_draft(draft.id) == final

    assert service.finalize(draft.id) == final
    workspace.prepare_confirmation.assert_called_once()
    confirm.assert_called_once()
    assert len(service.final_store.list_all()) == 1

    bundle.blueprint.tempo = 70
    bundle.audio_artifact.generation_spec.caption = "Changed after finalization."
    assert final.blueprint.tempo == 92
    assert final.audio_artifact.generation_spec.caption == "Warm instrumental music."


def test_prepare_or_confirm_failure_never_creates_final_creation(tmp_path):
    draft = _draft(uuid4())
    bundle = _bundle(draft)
    service, workspace, confirm, _ = _service(tmp_path, draft, bundle)
    workspace.prepare_confirmation.side_effect = ValueError("当前 BlueprintRevision 尚未生成音乐")

    with pytest.raises(ValueError, match="尚未生成音乐"):
        service.finalize(draft.id)
    confirm.assert_not_called()
    assert service.final_store.list_all() == []

    workspace.prepare_confirmation.side_effect = None
    confirm.side_effect = OSError("memory save failed")
    with pytest.raises(OSError, match="memory save failed"):
        service.finalize(draft.id)
    assert service.final_store.list_all() == []


def test_archive_failure_restores_draft_for_safe_retry(tmp_path, monkeypatch):
    draft = _draft(uuid4())
    bundle = _bundle(draft)
    service, _, confirm, restored_drafts = _service(tmp_path, draft, bundle)

    def fail_to_save(_final):
        raise OSError("final archive failed")

    monkeypatch.setattr(service.final_store, "save", fail_to_save)
    with pytest.raises(OSError, match="final archive failed"):
        service.finalize(draft.id)

    confirm.assert_called_once_with(draft.id)
    assert restored_drafts == [draft]
    assert service.final_store.list_all() == []


def test_memory_id_mismatch_restores_draft_and_fails(tmp_path):
    draft = _draft(uuid4())
    bundle = _bundle(draft)
    service, _, confirm, restored_drafts = _service(tmp_path, draft, bundle)
    confirm.return_value = MusicMemory(
        id=uuid4(),
        text=draft.text,
        emotion=draft.emotion,
        blueprint=draft.blueprint,
    )

    with pytest.raises(RuntimeError, match="ID 与 Draft 不一致"):
        service.finalize(draft.id)
    assert restored_drafts == [draft]
    assert service.final_store.list_all() == []

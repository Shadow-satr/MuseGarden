"""Step 13.8：显式当前音频选择测试，全部使用临时目录。"""

import json
from uuid import uuid4

import pytest

from music_engine import (
    AceStepGenerationResult,
    AudioStore,
    MusicGenerationSpec,
    MusicVersionService,
)


def _save(store, draft_id, revision_id, task_number):
    return store.save(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=MusicGenerationSpec(
            caption="Warm instrumental music with piano and strings.",
            duration_seconds=20,
            bpm=92,
            key="C Major",
            seed=task_number,
        ),
        generation_result=AceStepGenerationResult(
            task_id=f"ace-task-{task_number}",
            audio_bytes=f"RIFF-audio-{task_number}".encode(),
            content_type="audio/wav",
        ),
    )


def test_explicit_selection_pins_audio_and_clear_restores_latest(tmp_path):
    store = AudioStore(tmp_path)
    service = MusicVersionService(store)
    draft_id = uuid4()
    revision_id = uuid4()
    first = _save(store, draft_id, revision_id, 1)
    selected = _save(store, draft_id, revision_id, 2)
    latest = _save(store, draft_id, revision_id, 3)

    assert service.get_current_for_revision(revision_id) == latest
    metadata_before = store.metadata_file.read_bytes()
    audio_before = {
        path.name: path.read_bytes() for path in (tmp_path / "audio").glob("*.wav")
    }

    assert service.select_current(revision_id, selected.id) == selected
    assert json.loads(store.current_audio_file.read_text(encoding="utf-8")) == {
        str(revision_id): str(selected.id)
    }
    assert service.get_current_for_revision(revision_id) == selected
    assert MusicVersionService(AudioStore(tmp_path)).get_current_for_revision(revision_id) == selected
    assert store.metadata_file.read_bytes() == metadata_before
    assert {
        path.name: path.read_bytes() for path in (tmp_path / "audio").glob("*.wav")
    } == audio_before

    newer = _save(store, draft_id, revision_id, 4)
    assert service.get_current_for_revision(revision_id) == selected

    service.clear_current_selection(revision_id)
    assert service.get_current_for_revision(revision_id) == newer
    service.clear_current_selection(revision_id)
    assert service.get_current_for_revision(revision_id) == newer
    assert first.id != selected.id != latest.id != newer.id


def test_selection_rejects_missing_or_cross_revision_audio(tmp_path):
    store = AudioStore(tmp_path)
    service = MusicVersionService(store)
    draft_id = uuid4()
    revision_id = uuid4()
    other_revision_id = uuid4()
    _save(store, draft_id, revision_id, 1)
    other_artifact = _save(store, draft_id, other_revision_id, 2)

    with pytest.raises(ValueError, match="不存在"):
        service.select_current(revision_id, uuid4())
    with pytest.raises(ValueError, match="其他"):
        service.select_current(revision_id, other_artifact.id)


def test_stale_explicit_selection_reports_data_inconsistency(tmp_path):
    store = AudioStore(tmp_path)
    revision_id = uuid4()
    store.current_audio_file.write_text(
        json.dumps({str(revision_id): str(uuid4())}),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="不存在"):
        MusicVersionService(store).get_current_for_revision(revision_id)

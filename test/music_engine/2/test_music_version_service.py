"""Step 13.7：AudioArtifact 查询与当前音频规则测试。"""

import json
from datetime import datetime, timedelta
from uuid import uuid4

from unittest.mock import MagicMock

from ai_engine.memory.schema import BEIJING_TIMEZONE
from music_engine import (
    AceStepGenerationResult,
    AudioStore,
    MusicGenerationSpec,
    MusicVersionService,
)


def _spec() -> MusicGenerationSpec:
    return MusicGenerationSpec(
        caption="Warm instrumental music with piano and strings.",
        duration_seconds=20,
        bpm=92,
        key="C Major",
        instrumental=True,
        seed=20261006,
    )


def _save(store, draft_id, revision_id, task_number):
    return store.save(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=_spec(),
        generation_result=AceStepGenerationResult(
            task_id=f"ace-task-{task_number}",
            audio_bytes=f"RIFF-audio-{task_number}".encode(),
            content_type="audio/wav",
        ),
    )


def test_audio_store_filters_sorts_and_keeps_files_unchanged(tmp_path):
    store = AudioStore(tmp_path)
    draft_id = uuid4()
    revision_id = uuid4()
    other_revision_id = uuid4()
    other_draft_id = uuid4()
    first = _save(store, draft_id, revision_id, 1)
    second = _save(store, draft_id, revision_id, 2)
    third = _save(store, draft_id, revision_id, 3)
    other_revision = _save(store, draft_id, other_revision_id, 4)
    other_draft = _save(store, other_draft_id, uuid4(), 5)

    # 特意打乱 JSON 顺序并指定时间，证明查询依据 created_at，而不是数组位置。
    base_time = datetime(2026, 10, 6, 12, tzinfo=BEIJING_TIMEZONE)
    oldest = first.model_copy(update={"created_at": base_time})
    middle = second.model_copy(update={"created_at": base_time + timedelta(minutes=5)})
    newest = third.model_copy(update={"created_at": base_time + timedelta(minutes=10)})
    other_revision = other_revision.model_copy(
        update={"created_at": base_time + timedelta(minutes=15)}
    )
    other_draft = other_draft.model_copy(
        update={"created_at": base_time + timedelta(minutes=20)}
    )
    shuffled = [newest, other_draft, middle, other_revision, oldest]
    store.metadata_file.write_text(
        json.dumps([artifact.model_dump(mode="json") for artifact in shuffled]),
        encoding="utf-8",
    )

    metadata_before = store.metadata_file.read_bytes()
    audio_before = {
        path.name: path.read_bytes()
        for path in (tmp_path / "audio").glob("*.wav")
    }

    assert store.list_by_revision(uuid4()) == []
    assert store.get_latest_by_revision(uuid4()) is None
    assert store.list_by_revision(revision_id) == [oldest, middle, newest]
    assert store.list_by_draft(draft_id) == [oldest, middle, newest, other_revision]
    assert store.get_latest_by_revision(revision_id) == newest

    assert store.metadata_file.read_bytes() == metadata_before
    assert {
        path.name: path.read_bytes()
        for path in (tmp_path / "audio").glob("*.wav")
    } == audio_before


def test_music_version_service_delegates_to_audio_store():
    store = MagicMock(spec=AudioStore)
    revision_id = uuid4()
    draft_id = uuid4()
    store.get_selected_audio_id.return_value = None
    service = MusicVersionService(store)

    service.list_for_revision(revision_id)
    service.list_for_draft(draft_id)
    service.get_current_for_revision(revision_id)

    store.list_by_revision.assert_called_once_with(revision_id)
    store.list_by_draft.assert_called_once_with(draft_id)
    store.get_latest_by_revision.assert_called_once_with(revision_id)

"""Step 13.5：AudioStore 使用 pytest 临时目录，不触碰正式 database/local。"""

import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from music_engine import (
    AceStepGenerationResult,
    AudioStore,
    MusicGenerationSpec,
)


@pytest.fixture
def generation_spec() -> MusicGenerationSpec:
    return MusicGenerationSpec(
        caption="Warm instrumental music with piano and strings.",
        duration_seconds=20,
        bpm=92,
        key="C Major",
        instrumental=True,
        seed=20261006,
    )


@pytest.fixture
def generation_result() -> AceStepGenerationResult:
    return AceStepGenerationResult(
        task_id="ace-task-001",
        audio_bytes=b"RIFF-test-wav-bytes",
        content_type="audio/wav",
    )


def test_save_creates_audio_and_metadata(tmp_path, generation_spec, generation_result):
    store = AudioStore(tmp_path)
    draft_id = uuid4()
    revision_id = uuid4()

    artifact = store.save(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=generation_spec,
        generation_result=generation_result,
    )

    audio_path = tmp_path / artifact.file_path
    assert artifact.draft_id == draft_id
    assert artifact.revision_id == revision_id
    assert artifact.generation_spec == generation_spec
    assert artifact.provider == "ace_step"
    assert artifact.provider_task_id == "ace-task-001"
    assert artifact.content_type == "audio/wav"
    assert audio_path.name == f"{artifact.id}.wav"
    assert audio_path.exists()
    assert audio_path.read_bytes() == generation_result.audio_bytes

    metadata = json.loads((tmp_path / "audio_artifacts.json").read_text(encoding="utf-8"))
    assert metadata == [artifact.model_dump(mode="json")]
    assert "audio_bytes" not in metadata[0]

    assert store.get(artifact.id) == artifact
    assert store.load_audio(str(artifact.id)) == generation_result.audio_bytes


def test_each_save_creates_a_new_audio_file(tmp_path, generation_spec, generation_result):
    store = AudioStore(tmp_path)
    draft_id = uuid4()
    revision_id = uuid4()
    first = store.save(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=generation_spec,
        generation_result=generation_result,
    )
    second = store.save(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec=generation_spec,
        generation_result=generation_result,
    )

    assert first.id != second.id
    assert first.file_path != second.file_path
    assert first.draft_id == second.draft_id == draft_id
    assert first.revision_id == second.revision_id == revision_id
    assert (tmp_path / first.file_path).read_bytes() == generation_result.audio_bytes
    assert (tmp_path / second.file_path).read_bytes() == generation_result.audio_bytes


def test_metadata_failure_removes_new_audio_file(
    tmp_path, monkeypatch, generation_spec, generation_result
):
    store = AudioStore(tmp_path)

    def fail_to_write_metadata(_artifacts):
        raise OSError("metadata write failed")

    monkeypatch.setattr(store, "_write_artifacts", fail_to_write_metadata)

    with pytest.raises(OSError, match="metadata write failed"):
        store.save(
            draft_id=uuid4(),
            revision_id=uuid4(),
            generation_spec=generation_spec,
            generation_result=generation_result,
        )

    assert not list((tmp_path / "audio").iterdir())
    assert not (tmp_path / "audio_artifacts.json").exists()


def test_empty_audio_is_rejected_before_storage():
    with pytest.raises(ValidationError):
        AceStepGenerationResult(
            task_id="ace-task-empty",
            audio_bytes=b"",
            content_type="audio/wav",
        )

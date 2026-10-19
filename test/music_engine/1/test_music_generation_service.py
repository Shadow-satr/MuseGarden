"""Step 13.6：MusicGenerationService 编排测试，不调用真实 ACE-Step。"""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import BlueprintRevision
from music_engine.adapter import blueprint_to_generation_spec
from music_engine import (
    AceStepGenerationResult,
    AudioStore,
    MusicGenerationService,
)
from music_engine.providers.ace_step import AceStepClient, AceStepProviderError


@pytest.fixture
def revision() -> BlueprintRevision:
    return BlueprintRevision(
        draft_id=uuid4(),
        version=2,
        edit_instruction="整体更温柔一点。",
        blueprint=MusicBlueprint(
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
        ),
    )


@pytest.fixture
def provider_result() -> AceStepGenerationResult:
    return AceStepGenerationResult(
        task_id="ace-task-001",
        audio_bytes=b"RIFF-test-wav-bytes",
        content_type="audio/wav",
    )


def test_service_orchestrates_revision_to_audio_artifact(
    tmp_path, revision, provider_result
):
    client = MagicMock(spec=AceStepClient)
    client.generate_audio.return_value = provider_result
    store = AudioStore(tmp_path)
    service = MusicGenerationService(client, store)
    draft_id = uuid4()
    original_revision = revision.model_dump(mode="json")

    with (
        patch(
            "music_engine.service.blueprint_to_generation_spec",
            wraps=blueprint_to_generation_spec,
        ) as adapter,
        patch.object(store, "save", wraps=store.save) as save,
    ):
        artifact = service.generate_for_revision(
            draft_id=draft_id,
            revision=revision,
            duration_seconds=30,
            seed=20261006,
        )

    adapter.assert_called_once_with(
        revision.blueprint,
        duration_seconds=30,
        seed=20261006,
    )
    spec = client.generate_audio.call_args.args[0]
    assert spec.duration_seconds == 30
    assert spec.seed == 20261006
    assert spec.bpm == revision.blueprint.tempo
    assert spec.key == revision.blueprint.key

    save.assert_called_once()
    saved = save.call_args.kwargs
    assert saved["draft_id"] == draft_id
    assert saved["revision_id"] == revision.id
    assert saved["generation_spec"] is spec
    assert saved["generation_result"] is provider_result
    assert artifact.revision_id == revision.id
    assert (tmp_path / artifact.file_path).read_bytes() == provider_result.audio_bytes
    assert revision.model_dump(mode="json") == original_revision


def test_provider_and_storage_errors_propagate(revision, provider_result):
    provider_failure = MagicMock(spec=AceStepClient)
    provider_failure.generate_audio.side_effect = AceStepProviderError("service unavailable")
    store = MagicMock(spec=AudioStore)

    with pytest.raises(AceStepProviderError, match="service unavailable"):
        MusicGenerationService(provider_failure, store).generate_for_revision(
            draft_id=uuid4(), revision=revision
        )
    store.save.assert_not_called()

    client = MagicMock(spec=AceStepClient)
    client.generate_audio.return_value = provider_result
    storage_failure = MagicMock(spec=AudioStore)
    storage_failure.save.side_effect = OSError("disk write failed")

    with pytest.raises(OSError, match="disk write failed"):
        MusicGenerationService(client, storage_failure).generate_for_revision(
            draft_id=uuid4(), revision=revision
        )


def test_repeated_generation_creates_new_artifacts(tmp_path, revision, provider_result):
    client = MagicMock(spec=AceStepClient)
    client.generate_audio.return_value = provider_result
    service = MusicGenerationService(client, AudioStore(tmp_path))
    draft_id = uuid4()

    first = service.generate_for_revision(draft_id=draft_id, revision=revision)
    second = service.generate_for_revision(draft_id=draft_id, revision=revision)

    assert first.id != second.id
    assert first.file_path != second.file_path
    assert first.revision_id == second.revision_id == revision.id
    assert client.generate_audio.call_count == 2

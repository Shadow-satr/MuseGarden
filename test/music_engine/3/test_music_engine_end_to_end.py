"""Step 13.12：使用真实本地 Store 与 Fake Provider 的完整 Music Engine 闭环测试。"""

from pathlib import Path

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation import (
    CreationDraft,
    edit_creation_draft,
    load_drafts,
    load_revisions,
    start_creation,
)
from ai_engine.memory import load_memories
from ai_engine.memory.schema import EmotionSnapshot
from music_engine import (
    AceStepGenerationResult,
    AudioStore,
    CreationFinalizationService,
    FinalCreationStore,
    MusicGenerationService,
    MusicVersionService,
    MusicWorkspaceService,
)


class FakeAceStepClient:
    """替代本地模型：保留 Service 输入输出契约，但不发出 HTTP 请求。"""

    def __init__(self) -> None:
        self.calls = []

    def generate_audio(self, spec):
        self.calls.append(spec)
        number = len(self.calls)
        return AceStepGenerationResult(
            task_id=f"fake-ace-task-{number}",
            audio_bytes=f"RIFF-fake-wav-{number}".encode(),
            content_type="audio/wav",
        )


def _blueprint(tempo: int = 108, texture: str = "warm") -> MusicBlueprint:
    return MusicBlueprint(
        primary_emotion="满足感",
        secondary_emotions=["疲劳"],
        energy=0.55,
        valence=0.8,
        tempo=tempo,
        key="C Major",
        instruments=["piano", "strings"],
        texture=texture,
        scene="比赛结束之后",
        progression="calm_to_rising",
    )


def _patch_ai_storage(monkeypatch, data_root: Path):
    import ai_engine.creation.revision_store as revision_store
    import ai_engine.creation.store as draft_store
    import ai_engine.memory.store as memory_store

    monkeypatch.setattr(draft_store, "DRAFT_FILE", data_root / "drafts.json")
    monkeypatch.setattr(revision_store, "REVISION_FILE", data_root / "revisions.json")
    monkeypatch.setattr(memory_store, "MEMORY_FILE", data_root / "memories.json")


def test_full_creation_flow_uses_final_revision_and_pinned_audio(tmp_path, monkeypatch):
    ai_data = tmp_path / "ai_data"
    music_data = tmp_path / "music_data"
    _patch_ai_storage(monkeypatch, ai_data)

    initial_blueprint = _blueprint()
    created_draft = CreationDraft(
        text="比赛终于结束了，有点累，但很满足。",
        emotion=EmotionSnapshot(
            primary_emotion="满足感",
            secondary_emotions=["疲劳"],
            scene="比赛结束之后",
        ),
        blueprint=initial_blueprint,
    )
    monkeypatch.setattr(
        "ai_engine.creation.manager.run_creation_pipeline",
        lambda **_kwargs: created_draft,
    )

    # 正式创建流程保存 Draft 和 Revision V1；不调用真实 LLM。
    draft = start_creation(created_draft.text, use_memory=False)
    revisions_v1 = load_revisions(draft.id)
    assert len(revisions_v1) == 1
    assert revisions_v1[0].version == 1

    provider = FakeAceStepClient()
    audio_store = AudioStore(music_data)
    workspace = MusicWorkspaceService(
        MusicGenerationService(provider, audio_store),
        MusicVersionService(audio_store),
    )

    # V1 正式生成并持久化第一份音频。
    v1_audio = workspace.generate_current(draft.id, seed=101)
    assert (music_data / v1_audio.file_path).read_bytes() == b"RIFF-fake-wav-1"

    # 用正式编辑生命周期创建 V2，而不是原地改 V1。
    v2_blueprint = _blueprint(tempo=82, texture="soft")
    monkeypatch.setattr(
        "ai_engine.creation.manager.edit_blueprint",
        lambda **_kwargs: v2_blueprint,
    )
    updated_draft = edit_creation_draft(draft.id, "再温柔一点，钢琴明显一点。")
    revisions = load_revisions(draft.id)
    assert [revision.version for revision in revisions] == [1, 2]
    current_revision = revisions[-1]
    assert current_revision.blueprint == updated_draft.blueprint == v2_blueprint

    # 新 Revision 不继承 V1 音频，必须自行生成。
    assert workspace.get_current_audio(draft.id) is None
    v2_audio_a = workspace.generate_current(draft.id, duration_seconds=20, seed=202)
    v2_audio_b = workspace.generate_current(draft.id, duration_seconds=20, seed=303)
    assert v1_audio.revision_id != current_revision.id
    assert v2_audio_a.revision_id == v2_audio_b.revision_id == current_revision.id
    assert len(workspace.list_current_revision_audio(draft.id)) == 2

    # pin 较早的 V2 候选；确认包和最终成果必须使用它，而不是 latest B。
    workspace.select_audio(draft.id, v2_audio_a.id)
    bundle = workspace.prepare_confirmation(draft.id)
    assert bundle.revision_id == current_revision.id
    assert bundle.audio_artifact.id == v2_audio_a.id
    assert bundle.audio_artifact.id != v2_audio_b.id

    final_store = FinalCreationStore(music_data)
    finalizer = CreationFinalizationService(workspace, final_store)
    final = finalizer.finalize(draft.id)

    assert final.revision_id == current_revision.id
    assert final.blueprint == current_revision.blueprint
    assert final.audio_artifact.id == v2_audio_a.id
    assert final.memory_id == draft.id
    assert final_store.get(final.id) == final
    assert final_store.get_by_draft(draft.id) == final
    assert (music_data / "audio_artifacts.json").exists()
    assert (music_data / v2_audio_a.file_path).exists()
    assert not load_drafts()
    assert load_revisions(draft.id) == revisions
    memories = load_memories()
    assert len(memories) == 1
    assert memories[0].id == draft.id
    assert memories[0].blueprint == current_revision.blueprint
    assert provider.calls[0].bpm == 108
    assert provider.calls[-1].bpm == 82

    # FinalCreation 已存在时，即使 Draft 已删除，重复最终确认也应安全返回已有成果。
    assert finalizer.finalize(draft.id) == final
    assert len(final_store.list_all()) == 1

"""
测试最终 Blueprint 确认时的版本一致性。

使用临时 Draft、Revision 和 Memory 文件，
不调用 LLM，也不写入项目真实数据。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation import (
    BlueprintRevision,
    CreationDraft,
    confirm_draft,
    load_drafts,
    load_revisions,
    save_draft,
    save_revision,
    update_draft_blueprint,
)
from ai_engine.memory import commit_memory, load_memories
from test.output_format import format_record


emotion = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "scene": "completed_competition",
}
blueprint_v1 = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.8,
    valence=0.8,
    tempo=110,
    key="C Major",
    instruments=["piano", "guitar"],
    texture="bright",
    scene="celebration",
    progression="calm_to_rising",
)
blueprint_v2 = MusicBlueprint(
    **{
        **blueprint_v1.model_dump(),
        "energy": 0.4,
        "tempo": 82,
        "texture": "soft",
    }
)
blueprint_v3 = MusicBlueprint(
    **{
        **blueprint_v2.model_dump(),
        "instruments": ["piano", "strings"],
    }
)


def make_draft(blueprint: MusicBlueprint, text: str) -> CreationDraft:
    """创建一份尚未确认的草稿。"""
    draft = CreationDraft(text=text, emotion=emotion, blueprint=blueprint)
    save_draft(draft)
    return draft


def save_history(draft: CreationDraft, revisions: list[tuple[int, MusicBlueprint, str | None]]):
    """为草稿保存指定的版本历史。"""
    for version, blueprint, instruction in revisions:
        save_revision(
            BlueprintRevision(
                draft_id=draft.id,
                version=version,
                edit_instruction=instruction,
                blueprint=blueprint,
            )
        )


# 初始 V1 与直接切回的 V2，都应确认当前最终 Blueprint。
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    memory_file = temporary_root / "database" / "local" / "memories.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch("ai_engine.memory.store.MEMORY_FILE", memory_file),
        patch("ai_engine.creation.manager.edit_blueprint") as mock_editor,
    ):
        # 只有 Version 1 的创作可以正常确认。
        initial_draft = make_draft(blueprint_v1, "初始版本确认测试。")
        save_history(initial_draft, [(1, blueprint_v1, None)])
        initial_memory = confirm_draft(initial_draft.id)
        assert initial_memory.blueprint == blueprint_v1
        assert load_drafts() == []
        assert [revision.version for revision in load_revisions(initial_draft.id)] == [1]

        # V1、V2、V3 中直接切回 V2；最终确认必须保存 V2 的 Blueprint。
        final_draft = make_draft(blueprint_v1, "恢复后确认测试。")
        save_history(
            final_draft,
            [
                (1, blueprint_v1, None),
                (2, blueprint_v2, "节奏慢一点。"),
                (3, blueprint_v3, "加入弦乐。"),
            ],
        )
        update_draft_blueprint(final_draft.id, blueprint_v2)
        final_draft = load_drafts()[0]
        history_before_confirmation = load_revisions(final_draft.id)

        final_memory = confirm_draft(final_draft.id)
        assert final_memory.id == final_draft.id
        assert final_memory.blueprint == blueprint_v2
        assert final_memory.blueprint == history_before_confirmation[1].blueprint
        assert load_drafts() == []
        assert load_revisions(final_draft.id) == history_before_confirmation
        assert len(load_revisions(final_draft.id)) == 3
        mock_editor.assert_not_called()

        print("Final Confirmed Memory:")
        print(format_record(final_memory.model_dump(mode="json")))


# 不一致、Memory 保存失败和旧版无 Revision Draft 的行为。
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    memory_file = temporary_root / "database" / "local" / "memories.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch("ai_engine.memory.store.MEMORY_FILE", memory_file),
    ):
        # Draft 与最新 Revision 不一致时，不能写入 Memory 或删除 Draft。
        mismatched_draft = make_draft(blueprint_v2, "不一致确认测试。")
        save_history(mismatched_draft, [(1, blueprint_v1, None)])
        try:
            confirm_draft(mismatched_draft.id)
            raise AssertionError("不一致状态应该被拒绝。")
        except ValueError:
            assert load_drafts() == [mismatched_draft]
            assert load_memories() == []
            assert [revision.version for revision in load_revisions(mismatched_draft.id)] == [1]

        # Memory 保存失败时，Draft 保持不变。
        failed_draft = make_draft(blueprint_v1, "Memory 保存失败测试。")
        save_history(failed_draft, [(1, blueprint_v1, None)])
        with patch(
            "ai_engine.creation.manager.commit_memory",
            side_effect=OSError("Memory 文件无法写入"),
        ):
            try:
                confirm_draft(failed_draft.id)
                raise AssertionError("Memory 保存失败应该暴露异常。")
            except OSError:
                assert failed_draft in load_drafts()
                assert load_memories() == []

        # 没有 Revision 的旧版 Draft 保持原有确认行为。
        legacy_draft = make_draft(blueprint_v1, "旧版草稿确认测试。")
        legacy_memory = confirm_draft(legacy_draft.id)
        assert legacy_memory.blueprint == blueprint_v1
        assert not any(draft.id == legacy_draft.id for draft in load_drafts())


# Draft 删除失败后重试不重复保存 Memory；同 ID 内容冲突应拒绝。
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    memory_file = temporary_root / "database" / "local" / "memories.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch("ai_engine.memory.store.MEMORY_FILE", memory_file),
    ):
        retry_draft = make_draft(blueprint_v1, "删除失败重试测试。")
        save_history(retry_draft, [(1, blueprint_v1, None)])

        with patch(
            "ai_engine.creation.manager.delete_draft",
            side_effect=OSError("草稿文件无法删除"),
        ):
            try:
                confirm_draft(retry_draft.id)
                raise AssertionError("Draft 删除失败应该暴露异常。")
            except OSError:
                assert retry_draft in load_drafts()

        saved_memory = load_memories()[0]
        retried_memory = confirm_draft(retry_draft.id)
        assert retried_memory == saved_memory
        assert load_memories() == [saved_memory]
        assert load_drafts() == []

        conflict_draft = make_draft(blueprint_v1, "内容冲突确认测试。")
        commit_memory(
            text=conflict_draft.text,
            emotion=conflict_draft.emotion,
            blueprint=blueprint_v2,
            memory_id=conflict_draft.id,
        )
        try:
            confirm_draft(conflict_draft.id)
            raise AssertionError("同 ID 内容冲突的 Memory 应该被拒绝。")
        except ValueError:
            assert conflict_draft in load_drafts()

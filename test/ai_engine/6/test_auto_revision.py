"""
测试 AI 修改草稿时的自动历史版本记录。

使用 Mock 模拟 AI Blueprint Editor，
使用临时 JSON 文件，不写入项目真实数据。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
import ai_engine.creation.manager as creation_manager
from ai_engine.creation import (
    BlueprintRevision,
    CreationDraft,
    edit_creation_draft,
    load_drafts,
    load_revisions,
    save_draft,
    save_revision,
    update_draft_blueprint,
)
from ai_engine.memory import commit_memory
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


def create_draft_with_version_one(text: str = "今天比赛结束了，虽然很累但是很满足。"):
    """创建已保存 Draft，并手动建立初始 Version 1。"""
    draft = CreationDraft(
        text=text,
        emotion=emotion,
        blueprint=blueprint_v1,
    )
    save_draft(draft)
    save_revision(
        BlueprintRevision(
            draft_id=draft.id,
            version=1,
            blueprint=draft.blueprint,
        )
    )
    return draft


# 正常连续修改：Version 1、2、3 都应保留
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
        draft = create_draft_with_version_one()

        with (
            patch(
                "ai_engine.creation.manager.edit_blueprint",
                side_effect=[blueprint_v2, blueprint_v3],
            ) as mock_editor,
            patch("ai_engine.creation.manager.commit_memory") as mock_commit,
        ):
            updated_v2 = edit_creation_draft(
                draft.id,
                "节奏慢一点，整体温柔一些。",
            )
            updated_v3 = edit_creation_draft(
                draft.id,
                "钢琴保留，去掉吉他。",
            )

            assert mock_editor.call_count == 2
            mock_commit.assert_not_called()

        history = load_revisions(draft.id)
        assert [revision.version for revision in history] == [1, 2, 3]
        assert history[0].blueprint == blueprint_v1
        assert history[1].blueprint == blueprint_v2
        assert history[2].blueprint == blueprint_v3
        assert history[1].edit_instruction == "节奏慢一点，整体温柔一些。"
        assert history[2].edit_instruction == "钢琴保留，去掉吉他。"
        assert all(revision.draft_id == draft.id for revision in history)
        assert load_drafts() == [updated_v3]
        assert updated_v2.id == updated_v3.id == draft.id
        assert updated_v3.text == draft.text
        assert updated_v3.emotion == draft.emotion
        assert updated_v3.created_at == draft.created_at
        assert updated_v3.blueprint == blueprint_v3

        # AI 编辑失败时，不修改 Draft，也不新增编辑版本
        with patch(
            "ai_engine.creation.manager.edit_blueprint",
            side_effect=ValueError("模型输出无效"),
        ):
            try:
                edit_creation_draft(draft.id, "再慢一点")
                raise AssertionError("AI 编辑失败应该暴露异常。")
            except ValueError:
                assert load_drafts() == [updated_v3]
                assert len(load_revisions(draft.id)) == 3

        # 已确认的 Draft 不能继续修改，也不调用编辑器
        confirmed_draft = CreationDraft(
            text="已经确认的创作。",
            emotion=emotion,
            blueprint=blueprint_v1,
        )
        save_draft(confirmed_draft)
        save_revision(
            BlueprintRevision(
                draft_id=confirmed_draft.id,
                version=1,
                blueprint=confirmed_draft.blueprint,
            )
        )
        commit_memory(
            text=confirmed_draft.text,
            emotion=confirmed_draft.emotion,
            blueprint=confirmed_draft.blueprint,
            memory_id=confirmed_draft.id,
        )

        with patch("ai_engine.creation.manager.edit_blueprint") as mock_editor:
            try:
                edit_creation_draft(confirmed_draft.id, "加入弦乐")
                raise AssertionError("已确认的草稿应该被拒绝。")
            except ValueError:
                mock_editor.assert_not_called()

        print("Current Draft After Version 3:")
        print(format_record(updated_v3.model_dump(mode="json")))


# 旧版无历史草稿：编辑前先自动创建 Version 1，再生成 Version 2
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    old_draft = CreationDraft(
        text="旧版草稿没有历史版本。",
        emotion=emotion,
        blueprint=blueprint_v1,
    )

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch(
            "ai_engine.creation.manager.edit_blueprint",
            return_value=blueprint_v2,
        ),
    ):
        save_draft(old_draft)
        edit_creation_draft(old_draft.id, "节奏慢一点")
        assert [revision.version for revision in load_revisions(old_draft.id)] == [1, 2]


# Draft 更新或 Revision 保存失败时，不留下错误的编辑历史
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
    ):
        draft = create_draft_with_version_one("失败保护测试。")

        with (
            patch(
                "ai_engine.creation.manager.edit_blueprint",
                return_value=blueprint_v2,
            ),
            patch(
                "ai_engine.creation.manager.update_draft_blueprint",
                side_effect=OSError("草稿文件无法写入"),
            ),
            patch("ai_engine.creation.manager.save_revision") as mock_save_revision,
        ):
            try:
                edit_creation_draft(draft.id, "节奏慢一点")
                raise AssertionError("Draft 更新失败应该暴露异常。")
            except OSError:
                mock_save_revision.assert_not_called()
                assert load_revisions(draft.id)[0].version == 1

        # Revision 保存失败后，应将 Draft 恢复到修改前的 Blueprint
        with (
            patch(
                "ai_engine.creation.manager.edit_blueprint",
                return_value=blueprint_v2,
            ),
            patch(
                "ai_engine.creation.manager.save_revision",
                side_effect=OSError("历史版本文件无法写入"),
            ),
        ):
            try:
                edit_creation_draft(draft.id, "节奏慢一点")
                raise AssertionError("Revision 保存失败应该暴露异常。")
            except OSError:
                assert load_drafts() == [draft]
                assert [revision.version for revision in load_revisions(draft.id)] == [1]


# Revision 保存后回滚也失败时，必须明确报告数据可能不一致
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
    ):
        draft = create_draft_with_version_one("回滚失败保护测试。")
        original_update = creation_manager.update_draft_blueprint

        def update_then_fail(*args, **kwargs):
            nonlocal_call_count[0] += 1
            if nonlocal_call_count[0] == 1:
                return original_update(*args, **kwargs)
            raise OSError("草稿回滚无法写入")

        nonlocal_call_count = [0]
        with (
            patch(
                "ai_engine.creation.manager.edit_blueprint",
                return_value=blueprint_v2,
            ),
            patch(
                "ai_engine.creation.manager.save_revision",
                side_effect=OSError("历史版本文件无法写入"),
            ),
            patch(
                "ai_engine.creation.manager.update_draft_blueprint",
                side_effect=update_then_fail,
            ),
        ):
            try:
                edit_creation_draft(draft.id, "节奏慢一点")
                raise AssertionError("回滚失败应该明确暴露异常。")
            except RuntimeError as error:
                assert "草稿回滚失败" in str(error)
                assert load_drafts()[0].blueprint == blueprint_v2


# 当前 Draft 与最新 Revision 不一致时，不能继续调用 AI 编辑器
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
    ):
        draft = create_draft_with_version_one("不一致状态测试。")
        # 模拟底层直接更新了 Draft，但尚未写入对应 Revision 的异常旧状态。
        update_draft_blueprint(draft.id, blueprint_v2)

        with patch("ai_engine.creation.manager.edit_blueprint") as mock_editor:
            try:
                edit_creation_draft(draft.id, "再温柔一点")
                raise AssertionError("不一致的草稿状态应该被拒绝。")
            except ValueError:
                mock_editor.assert_not_called()

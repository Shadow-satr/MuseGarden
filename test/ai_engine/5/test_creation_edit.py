"""
测试 AI 辅助创作草稿修改服务。

使用 Mock 模拟 Blueprint Editor，
使用临时 JSON 文件，不写入项目真实数据。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
import ai_engine.creation.manager as creation_manager
from ai_engine.creation import (
    CreationDraft,
    confirm_draft,
    edit_creation_draft,
    load_drafts,
    save_draft,
)
from ai_engine.memory import commit_memory
from test.output_format import format_record


emotion = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "scene": "completed_competition",
}
original_blueprint = MusicBlueprint(
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
edited_blueprint = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.4,
    valence=0.7,
    tempo=82,
    key="C Major",
    instruments=["piano", "strings"],
    texture="soft",
    scene="celebration",
    progression="calm_to_rising",
)
first_draft = CreationDraft(
    text="今天终于完成比赛了，虽然很累，但是感觉很值得。",
    emotion=emotion,
    blueprint=original_blueprint,
)
second_draft = CreationDraft(
    text="晚上想为自己做一首安静的音乐。",
    emotion=emotion,
    blueprint=original_blueprint,
)


# 临时目录会在测试结束后自动删除
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    memory_file = temporary_root / "database" / "local" / "memories.json"

    # 两种存储都改为临时路径，不污染项目真实 JSON 文件
    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.memory.store.MEMORY_FILE", memory_file),
    ):
        save_draft(first_draft)
        save_draft(second_draft)

        # 正常修改：编辑器得到正确输入，新 Blueprint 写回同一份 Draft
        with (
            patch(
                "ai_engine.creation.manager.edit_blueprint",
                return_value=edited_blueprint,
            ) as mock_editor,
            patch(
                "ai_engine.creation.manager.update_draft_blueprint",
                wraps=creation_manager.update_draft_blueprint,
            ) as mock_update,
            patch("ai_engine.creation.manager.commit_memory") as mock_commit,
        ):
            updated_draft = edit_creation_draft(
                first_draft.id,
                "节奏再慢一点，整体温柔一些。",
            )

            mock_editor.assert_called_once_with(
                original_text=first_draft.text,
                current_blueprint=first_draft.blueprint,
                edit_instruction="节奏再慢一点，整体温柔一些。",
            )
            mock_update.assert_called_once_with(first_draft.id, edited_blueprint)
            mock_commit.assert_not_called()

        assert updated_draft.id == first_draft.id
        assert updated_draft.text == first_draft.text
        assert updated_draft.emotion == first_draft.emotion
        assert updated_draft.created_at == first_draft.created_at
        assert updated_draft.blueprint == edited_blueprint
        assert load_drafts() == [updated_draft, second_draft]

        # 不存在的草稿和空修改要求不应调用 AI 编辑器
        with patch("ai_engine.creation.manager.edit_blueprint") as mock_editor:
            try:
                edit_creation_draft(uuid4(), "节奏慢一点")
                raise AssertionError("不存在的草稿应该被拒绝。")
            except ValueError:
                mock_editor.assert_not_called()

            try:
                edit_creation_draft(first_draft.id, "   ")
                raise AssertionError("空修改要求应该被拒绝。")
            except ValueError:
                mock_editor.assert_not_called()

        # AI 修改失败时，原始草稿必须保持不变
        with patch(
            "ai_engine.creation.manager.edit_blueprint",
            side_effect=ValueError("模型输出 JSON 格式错误"),
        ):
            try:
                edit_creation_draft(first_draft.id, "更温柔一点")
                raise AssertionError("AI 修改失败应该暴露异常。")
            except ValueError:
                assert load_drafts() == [updated_draft, second_draft]

        # 即使 Mock 返回非法 Blueprint，也不能写入草稿
        invalid_blueprint = {
            **edited_blueprint.model_dump(),
            "energy": 1.2,
        }
        with patch(
            "ai_engine.creation.manager.edit_blueprint",
            return_value=invalid_blueprint,
        ):
            try:
                edit_creation_draft(first_draft.id, "更柔和一点")
                raise AssertionError("非法 Blueprint 应该被拒绝。")
            except ValidationError:
                assert load_drafts() == [updated_draft, second_draft]

        # 已确认的 Draft 不能继续修改，也不调用 AI 编辑器
        commit_memory(
            text=second_draft.text,
            emotion=second_draft.emotion,
            blueprint=second_draft.blueprint,
            memory_id=second_draft.id,
        )

        with patch("ai_engine.creation.manager.edit_blueprint") as mock_editor:
            try:
                edit_creation_draft(second_draft.id, "加入钢琴")
                raise AssertionError("已确认的草稿不应该继续修改。")
            except ValueError:
                mock_editor.assert_not_called()

        # 原有确认功能仍可确认修改后的草稿
        confirmed_memory = confirm_draft(updated_draft.id)
        assert confirmed_memory.blueprint == edited_blueprint

        print("AI Edited Draft:")
        print(format_record(updated_draft.model_dump(mode="json")))

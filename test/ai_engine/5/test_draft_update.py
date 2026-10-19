"""
测试 CreationDraft Blueprint 更新服务。

使用临时 drafts.json 和 memories.json，
不写入项目真实的本地数据文件。
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
from ai_engine.creation import (
    CreationDraft,
    confirm_draft,
    load_drafts,
    save_draft,
    update_draft_blueprint,
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
new_blueprint = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.4,
    valence=0.7,
    tempo=85,
    key="A Minor",
    instruments=["piano", "strings"],
    texture="soft",
    scene="quiet_room",
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

        # 正常更新只替换 Blueprint，其余字段保持不变
        with patch("ai_engine.memory.manager.commit_memory") as mock_commit_memory:
            updated_draft = update_draft_blueprint(first_draft.id, new_blueprint)
            mock_commit_memory.assert_not_called()

        assert updated_draft.id == first_draft.id
        assert updated_draft.text == first_draft.text
        assert updated_draft.emotion == first_draft.emotion
        assert updated_draft.created_at == first_draft.created_at
        assert updated_draft.blueprint == new_blueprint
        assert load_drafts() == [updated_draft, second_draft]

        # 不存在的草稿和无效 Blueprint 都应被拒绝
        try:
            update_draft_blueprint(uuid4(), new_blueprint)
            raise AssertionError("不存在的草稿应该被拒绝。")
        except ValueError:
            pass

        invalid_blueprint = {
            **new_blueprint.model_dump(),
            "energy": 1.2,
        }

        try:
            update_draft_blueprint(first_draft.id, invalid_blueprint)
            raise AssertionError("无效 Blueprint 应该被拒绝。")
        except ValidationError:
            assert load_drafts() == [updated_draft, second_draft]

        # 持久化更新失败时，原始草稿数据应保持不变
        with patch(
            "ai_engine.creation.manager.replace_draft",
            side_effect=OSError("草稿文件无法写入"),
        ):
            try:
                update_draft_blueprint(first_draft.id, original_blueprint)
                raise AssertionError("更新失败应该暴露异常。")
            except OSError:
                assert load_drafts() == [updated_draft, second_draft]

        # 已存在同 ID 长期 Memory 的草稿不能继续修改
        commit_memory(
            text=second_draft.text,
            emotion=second_draft.emotion,
            blueprint=second_draft.blueprint,
            memory_id=second_draft.id,
        )

        try:
            update_draft_blueprint(second_draft.id, new_blueprint)
            raise AssertionError("已确认的草稿不应该继续修改。")
        except ValueError:
            assert load_drafts() == [updated_draft, second_draft]

        # 更新后的草稿仍可以正常确认，并提交更新后的 Blueprint
        confirmed_memory = confirm_draft(updated_draft.id)
        assert confirmed_memory.blueprint == new_blueprint
        assert load_drafts() == [second_draft]

        print("Updated Draft:")
        print(format_record(updated_draft.model_dump(mode="json")))

"""
测试 CreationDraft 确认服务。

使用临时 drafts.json 和 memories.json，
不写入项目真实的本地数据文件。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation import (
    CreationDraft,
    confirm_draft,
    load_drafts,
    save_draft,
)
from ai_engine.memory import load_memories
from test.output_format import format_record


emotion = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "scene": "completed_competition",
}
blueprint = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.8,
    valence=0.8,
    tempo=108,
    key="C Major",
    instruments=["piano", "strings"],
    texture="warm",
    scene="celebration",
    progression="calm_to_rising",
)
first_draft = CreationDraft(
    text="今天终于完成比赛了，虽然很累，但是感觉很值得。",
    emotion=emotion,
    blueprint=blueprint,
)
second_draft = CreationDraft(
    text="晚上想为自己做一首安静的音乐。",
    emotion=emotion,
    blueprint=blueprint,
)
third_draft = CreationDraft(
    text="明天想开始一段新的旅行。",
    emotion=emotion,
    blueprint=blueprint,
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
        save_draft(third_draft)

        # 正常确认后，Memory 保存成功且对应 Draft 被移除
        memory = confirm_draft(str(first_draft.id))
        assert memory.id == first_draft.id
        assert memory.text == first_draft.text
        assert memory.emotion == first_draft.emotion
        assert memory.blueprint == first_draft.blueprint
        assert load_memories() == [memory]
        assert load_drafts() == [second_draft, third_draft]

        # 重复确认已删除的 Draft 不会产生重复 Memory
        try:
            confirm_draft(first_draft.id)
            raise AssertionError("已确认的草稿不应该重复提交。")
        except ValueError:
            assert load_memories() == [memory]

        # 不存在的 Draft ID 必须明确报错
        try:
            confirm_draft(uuid4())
            raise AssertionError("不存在的草稿应该被拒绝。")
        except ValueError:
            pass

        # Memory 保存失败时，草稿必须保留
        with patch(
            "ai_engine.creation.manager.commit_memory",
            side_effect=OSError("Memory 文件无法写入"),
        ):
            try:
                confirm_draft(second_draft.id)
                raise AssertionError("Memory 保存失败应该暴露异常。")
            except OSError:
                assert second_draft in load_drafts()
                assert load_memories() == [memory]

        # Draft 删除失败时，不能伪装成确认成功；但 Memory 会保留
        with patch(
            "ai_engine.creation.manager.delete_draft",
            side_effect=OSError("Draft 文件无法写入"),
        ):
            try:
                confirm_draft(third_draft.id)
                raise AssertionError("Draft 删除失败应该暴露异常。")
            except OSError:
                assert third_draft in load_drafts()

        memories_after_failed_delete = load_memories()
        assert len(memories_after_failed_delete) == 2
        third_memory = next(
            saved_memory
            for saved_memory in memories_after_failed_delete
            if saved_memory.id == third_draft.id
        )

        # 重试时识别已保存的同 ID Memory，只完成草稿删除，不重复保存
        retried_memory = confirm_draft(third_draft.id)
        assert retried_memory == third_memory
        assert load_memories() == memories_after_failed_delete
        assert load_drafts() == [second_draft]

        print("Confirmed Memory:")
        print(format_record(memory.model_dump(mode="json")))

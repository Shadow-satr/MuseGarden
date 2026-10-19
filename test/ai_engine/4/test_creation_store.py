"""
测试 CreationDraft 本地 JSON 存储。

使用临时 drafts.json，
不写入项目真实的 database/local/drafts.json。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation import CreationDraft, load_drafts, save_draft
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


# 临时目录会在测试结束后自动删除
with TemporaryDirectory() as temporary_directory:
    draft_file = Path(temporary_directory) / "database" / "local" / "drafts.json"
    temporary_file = draft_file.with_name(f"{draft_file.name}.tmp")

    # 测试时替换默认路径，不写入项目真实 drafts.json
    with patch("ai_engine.creation.store.DRAFT_FILE", draft_file):
        # 文件不存在时应返回空列表
        assert load_drafts() == []

        # 保存草稿时不应调用长期 Memory 的 save_memory()
        with patch("ai_engine.memory.manager.save_memory") as mock_save_memory:
            save_draft(first_draft)
            save_draft(second_draft)
            mock_save_memory.assert_not_called()

        assert draft_file.exists()
        assert not temporary_file.exists()

        # 程序重新读取后，应恢复完整的 CreationDraft 对象
        loaded_drafts = load_drafts()
        assert loaded_drafts == [first_draft, second_draft]
        assert isinstance(loaded_drafts[0], CreationDraft)
        assert loaded_drafts[0].id == first_draft.id
        assert loaded_drafts[0].created_at == first_draft.created_at

        # 同一份草稿不能重复保存
        try:
            save_draft(first_draft)
            raise AssertionError("重复 id 的草稿应该被拒绝。")
        except ValueError:
            pass

        # 损坏 JSON 和无效草稿记录都必须明确报错
        draft_file.write_text("{损坏的 JSON", encoding="utf-8")

        try:
            load_drafts()
            raise AssertionError("损坏 JSON 应该被拒绝。")
        except ValueError:
            pass

        draft_file.write_text('[{"text": "缺少其他字段"}]', encoding="utf-8")

        try:
            load_drafts()
            raise AssertionError("无效草稿记录应该被拒绝。")
        except ValueError:
            pass

        print("Loaded Draft:")
        print(format_record(loaded_drafts[0].model_dump(mode="json")))

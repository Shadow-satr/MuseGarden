"""
测试 BlueprintRevision 本地存储。

使用临时 revisions.json，
不写入项目真实的历史版本、草稿或长期记忆文件。
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
from ai_engine.creation import BlueprintRevision, load_revisions, save_revision
from test.output_format import format_record


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
draft_a_id = uuid4()
draft_b_id = uuid4()
revision_a_v2 = BlueprintRevision(
    draft_id=draft_a_id,
    version=2,
    edit_instruction="节奏慢一点。",
    blueprint=blueprint,
)
revision_b_v1 = BlueprintRevision(
    draft_id=draft_b_id,
    version=1,
    blueprint=blueprint,
)
revision_a_v1 = BlueprintRevision(
    draft_id=draft_a_id,
    version=1,
    blueprint=blueprint,
)


# 临时目录会在测试结束后自动删除
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    memory_file = temporary_root / "database" / "local" / "memories.json"

    with patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file):
        # 文件不存在时，读取空列表
        assert load_revisions() == []

        # 多个 Draft 的版本可以共同保存，也不会覆盖已有历史版本
        save_revision(revision_a_v2)
        save_revision(revision_b_v1)
        save_revision(revision_a_v1)

        assert revision_file.exists()
        assert load_revisions() == [
            revision_a_v2,
            revision_b_v1,
            revision_a_v1,
        ]

        # 指定 Draft 的历史版本按 version 从小到大返回
        history_a = load_revisions(draft_a_id)
        assert history_a == [revision_a_v1, revision_a_v2]
        assert all(isinstance(revision, BlueprintRevision) for revision in history_a)
        assert history_a[0].blueprint == blueprint
        assert load_revisions(str(draft_b_id)) == [revision_b_v1]

        # 同一个 Draft 可以和其他 Draft 使用相同版本号
        assert revision_a_v1.version == revision_b_v1.version == 1

        # 同一 Draft 的重复版本号与重复 Revision ID 都应被拒绝
        duplicate_version = BlueprintRevision(
            draft_id=draft_a_id,
            version=1,
            blueprint=blueprint,
        )
        try:
            save_revision(duplicate_version)
            raise AssertionError("同一草稿的重复版本号应该被拒绝。")
        except ValueError:
            assert load_revisions(draft_a_id) == history_a

        try:
            save_revision(revision_a_v1)
            raise AssertionError("重复 Revision ID 应该被拒绝。")
        except ValueError:
            assert load_revisions(draft_a_id) == history_a

        # 非法 draft_id 和损坏 JSON 都必须明确报错
        try:
            load_revisions("not-a-uuid")
            raise AssertionError("非法草稿 ID 应该被拒绝。")
        except ValueError:
            pass

        revision_file.write_text("{invalid json", encoding="utf-8")
        try:
            load_revisions()
            raise AssertionError("损坏 JSON 应该被拒绝。")
        except ValueError:
            pass

        revision_file.write_text("{}", encoding="utf-8")
        try:
            load_revisions()
            raise AssertionError("不是列表的 JSON 根结构应该被拒绝。")
        except ValueError:
            pass

        # 无效 Revision 记录不能被加载为正常数据
        revision_file.write_text(
            '[{"draft_id": "not-a-uuid", "version": 1}]',
            encoding="utf-8",
        )
        try:
            load_revisions()
            raise AssertionError("无效 Revision 记录应该被拒绝。")
        except ValueError:
            pass

        # 恢复有效文件后，写入失败不能破坏原有历史版本
        revision_file.unlink()
        save_revision(revision_a_v1)
        existing_revisions = load_revisions()
        with patch(
            "ai_engine.creation.revision_store._write_revisions",
            side_effect=OSError("历史版本文件无法写入"),
        ):
            try:
                save_revision(revision_b_v1)
                raise AssertionError("写入失败应该暴露异常。")
            except OSError:
                assert load_revisions() == existing_revisions

        # Revision Store 不会创建草稿或长期记忆文件
        assert not draft_file.exists()
        assert not memory_file.exists()

        print("Draft A Revisions:")
        print(format_record(history_a[0].model_dump(mode="json")))

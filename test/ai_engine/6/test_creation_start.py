"""
测试正式创作开始服务。

使用 Mock 模拟 AI Pipeline，
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
from ai_engine.creation import (
    CreationDraft,
    load_drafts,
    load_revisions,
    start_creation,
)
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
draft = CreationDraft(
    text="今天比赛终于结束了，虽然很累，但是很满足。",
    emotion=emotion,
    blueprint=blueprint,
)


# 正常开始创作：同时保存 Draft 和 Version 1
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    memory_file = temporary_root / "database" / "local" / "memories.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch("ai_engine.memory.store.MEMORY_FILE", memory_file),
        patch(
            "ai_engine.creation.manager.run_creation_pipeline",
            return_value=draft,
        ) as mock_pipeline,
        patch("ai_engine.creation.manager.commit_memory") as mock_commit,
    ):
        started_draft = start_creation(
            text=draft.text,
            use_memory=False,
            top_k=2,
        )

        # 一次正式创作只调用一次 AI Pipeline，不调用长期 Memory 提交
        mock_pipeline.assert_called_once_with(
            text=draft.text,
            use_memory=False,
            top_k=2,
        )
        mock_commit.assert_not_called()

        assert started_draft == draft
        assert load_drafts() == [draft]

        history = load_revisions(draft.id)
        assert len(history) == 1
        initial_revision = history[0]
        assert initial_revision.draft_id == draft.id
        assert initial_revision.version == 1
        assert initial_revision.edit_instruction is None
        assert initial_revision.blueprint == draft.blueprint
        assert initial_revision.blueprint is not draft.blueprint

        # 同一 Draft 不能重复保存 Version 1
        try:
            start_creation(draft.text, use_memory=False, top_k=2)
            raise AssertionError("同一份草稿不应该重复开始创作。")
        except ValueError:
            assert load_revisions(draft.id) == [initial_revision]

        print("Started Creation Draft:")
        print(format_record(started_draft.model_dump(mode="json")))


# AI Pipeline 失败时，不应保存 Draft 或 Revision
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch(
            "ai_engine.creation.manager.run_creation_pipeline",
            side_effect=OSError("AI Pipeline 生成失败"),
        ),
    ):
        try:
            start_creation("这次创作无法生成")
            raise AssertionError("AI Pipeline 失败应该暴露异常。")
        except OSError:
            assert not draft_file.exists()
            assert not revision_file.exists()


# Draft 保存失败时，不应继续保存 Version 1
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    revision_file = temporary_root / "database" / "local" / "revisions.json"

    with (
        patch(
            "ai_engine.creation.manager.run_creation_pipeline",
            return_value=CreationDraft(
                text="草稿保存失败测试",
                emotion=emotion,
                blueprint=blueprint,
            ),
        ),
        patch(
            "ai_engine.creation.manager.save_draft",
            side_effect=OSError("草稿文件无法写入"),
        ),
        patch("ai_engine.creation.manager.save_revision") as mock_save_revision,
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
    ):
        try:
            start_creation("草稿保存失败测试")
            raise AssertionError("草稿保存失败应该暴露异常。")
        except OSError:
            mock_save_revision.assert_not_called()
            assert not revision_file.exists()


# Version 1 保存失败时，应尝试删除刚保存的 Draft
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    rollback_draft = CreationDraft(
        text="版本保存失败测试",
        emotion=emotion,
        blueprint=blueprint,
    )

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch(
            "ai_engine.creation.manager.run_creation_pipeline",
            return_value=rollback_draft,
        ),
        patch(
            "ai_engine.creation.manager.save_revision",
            side_effect=OSError("历史版本文件无法写入"),
        ),
    ):
        try:
            start_creation(rollback_draft.text)
            raise AssertionError("版本保存失败应该暴露异常。")
        except OSError:
            assert load_drafts() == []
            assert not revision_file.exists()


# 如果回滚也失败，必须明确暴露部分持久化失败，不能伪装成成功
with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    draft_file = temporary_root / "database" / "local" / "drafts.json"
    revision_file = temporary_root / "database" / "local" / "revisions.json"
    partial_draft = CreationDraft(
        text="回滚失败测试",
        emotion=emotion,
        blueprint=blueprint,
    )

    with (
        patch("ai_engine.creation.store.DRAFT_FILE", draft_file),
        patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file),
        patch(
            "ai_engine.creation.manager.run_creation_pipeline",
            return_value=partial_draft,
        ),
        patch(
            "ai_engine.creation.manager.save_revision",
            side_effect=OSError("历史版本文件无法写入"),
        ),
        patch(
            "ai_engine.creation.manager.delete_draft",
            side_effect=OSError("草稿文件无法删除"),
        ),
    ):
        try:
            start_creation(partial_draft.text)
            raise AssertionError("回滚失败应该明确暴露部分持久化错误。")
        except RuntimeError as error:
            assert "草稿回滚失败" in str(error)
            assert load_drafts() == [partial_draft]
            assert not revision_file.exists()

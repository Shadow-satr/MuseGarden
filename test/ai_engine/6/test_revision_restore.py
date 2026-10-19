"""测试恢复既有 BlueprintRevision：不复制版本，也不调用 LLM。"""

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
    BlueprintRevision,
    CreationDraft,
    edit_creation_draft,
    load_drafts,
    load_revisions,
    restore_blueprint_revision,
    save_draft,
    save_revision,
    update_draft_blueprint,
)
from ai_engine.memory import commit_memory


def _blueprint(tempo: int) -> MusicBlueprint:
    return MusicBlueprint(
        primary_emotion="achievement",
        secondary_emotions=["fatigue"],
        energy=0.6,
        valence=0.7,
        tempo=tempo,
        key="C Major",
        instruments=["piano", "strings"],
        texture="warm",
        scene="after a competition",
        progression="calm_to_rising",
    )


blueprint_v1 = _blueprint(92)
blueprint_v2 = _blueprint(80)
blueprint_v3 = _blueprint(108)


def _create_history() -> CreationDraft:
    draft = CreationDraft(
        text="今天终于完成比赛了。",
        emotion={"primary_emotion": "achievement", "secondary_emotions": [], "scene": "competition"},
        blueprint=blueprint_v1,
    )
    save_draft(draft)
    for version, blueprint in enumerate([blueprint_v1, blueprint_v2, blueprint_v3], 1):
        save_revision(BlueprintRevision(draft_id=draft.id, version=version, blueprint=blueprint))
    update_draft_blueprint(draft.id, blueprint_v3)
    return draft


with TemporaryDirectory() as temporary_directory:
    root = Path(temporary_directory)
    with (
        patch("ai_engine.creation.store.DRAFT_FILE", root / "drafts.json"),
        patch("ai_engine.creation.revision_store.REVISION_FILE", root / "revisions.json"),
        patch("ai_engine.memory.store.MEMORY_FILE", root / "memories.json"),
        patch("ai_engine.creation.manager.edit_blueprint") as mock_editor,
    ):
        draft = _create_history()

        restored = restore_blueprint_revision(draft.id, 1)
        assert restored.blueprint == blueprint_v1
        assert [item.version for item in load_revisions(draft.id)] == [1, 2, 3]
        mock_editor.assert_not_called()

        # 切回原 V1 后，下一次用户编辑才产生 V4。
        with patch("ai_engine.creation.manager.edit_blueprint", return_value=blueprint_v2):
            edited = edit_creation_draft(draft.id, "再柔和一点")
        assert edited.blueprint == blueprint_v2
        assert [item.version for item in load_revisions(draft.id)] == [1, 2, 3, 4]

        # 已经在目标版本时不改写数据。
        restored_again = restore_blueprint_revision(draft.id, 2)
        assert restored_again.blueprint == blueprint_v2
        assert [item.version for item in load_revisions(draft.id)] == [1, 2, 3, 4]

        for invalid_version in [0, -1, True, "1", 99]:
            try:
                restore_blueprint_revision(draft.id, invalid_version)
                raise AssertionError("非法或不存在版本应该被拒绝")
            except ValueError:
                pass

        # Draft 不属于历史时，仍允许直接切回一个真实历史版本。
        update_draft_blueprint(draft.id, _blueprint(70))
        assert restore_blueprint_revision(draft.id, 3).blueprint == blueprint_v3

        commit_memory(
            text=load_drafts()[0].text,
            emotion=load_drafts()[0].emotion,
            blueprint=load_drafts()[0].blueprint,
            memory_id=draft.id,
        )
        try:
            restore_blueprint_revision(draft.id, 1)
            raise AssertionError("已确认草稿不能恢复")
        except ValueError:
            pass

        try:
            restore_blueprint_revision(uuid4(), 1)
            raise AssertionError("不存在草稿应该被拒绝")
        except ValueError:
            pass

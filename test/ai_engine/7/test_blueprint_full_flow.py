"""
测试完整 Blueprint 创作流程。

创建 V1、修改为 V2 和 V3、再直接切回 V2、
对比版本并确认最终创作。全程使用 Mock 和临时 JSON 文件。
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
    compare_blueprint_revisions,
    confirm_draft,
    edit_creation_draft,
    load_drafts,
    load_revisions,
    restore_blueprint_revision,
    start_creation,
)
from ai_engine.memory import load_memories
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
draft = CreationDraft(
    text="今天终于完成比赛了，虽然很累，但是很满足。",
    emotion=emotion,
    blueprint=blueprint_v1,
)


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
        patch(
            "ai_engine.creation.manager.edit_blueprint",
            side_effect=[blueprint_v2, blueprint_v3],
        ) as mock_editor,
    ):
        # 创建 Draft 与 Version 1
        current_draft = start_creation(draft.text, use_memory=False, top_k=2)
        assert current_draft == draft
        assert [revision.version for revision in load_revisions(draft.id)] == [1]

        # 两次修改自动创建 Version 2、Version 3
        current_draft = edit_creation_draft(
            draft.id,
            "节奏慢一点，整体温柔一些。",
        )
        current_draft = edit_creation_draft(
            draft.id,
            "钢琴保留，去掉吉他。",
        )
        assert [revision.version for revision in load_revisions(draft.id)] == [1, 2, 3]
        assert current_draft.blueprint == blueprint_v3

        # 恢复 V2 是直接切回已有版本，不产生重复 V4。
        current_draft = restore_blueprint_revision(draft.id, target_version=2)
        history = load_revisions(draft.id)
        assert [revision.version for revision in history] == [1, 2, 3]
        assert current_draft.blueprint == blueprint_v2
        assert history[1].blueprint == blueprint_v2

        # 对比 V2 与 V3，确认发生的字段变化。
        differences = compare_blueprint_revisions(draft.id, 2, 3)
        assert differences["instruments"] == {
            "from": ["piano", "guitar"],
            "to": ["piano", "strings"],
        }

        # 最终确认保存当前 V2 的 Blueprint，移除 Draft，保留完整历史。
        memory = confirm_draft(draft.id)
        assert memory.id == draft.id
        assert memory.blueprint == blueprint_v2
        assert load_memories() == [memory]
        assert load_drafts() == []
        assert [revision.version for revision in load_revisions(draft.id)] == [1, 2, 3]
        assert mock_pipeline.call_count == 1
        assert mock_editor.call_count == 2

        print("Full Blueprint Flow Memory:")
        print(format_record(memory.model_dump(mode="json")))

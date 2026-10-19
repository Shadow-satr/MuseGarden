"""
测试 BlueprintRevision 字段差异比较。

只读取临时 revisions.json，
不创建 Draft，不调用 LLM，也不写入任何历史记录。
"""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation import (
    BlueprintRevision,
    compare_blueprint_revisions,
    save_revision,
)
from test.output_format import format_record


blueprint_v1 = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.4,
    valence=0.7,
    tempo=85,
    key="C Major",
    instruments=["piano", "guitar"],
    texture="soft",
    scene="celebration",
    progression="calm_to_rising",
)
blueprint_v2 = MusicBlueprint(
    **{
        **blueprint_v1.model_dump(),
        "primary_emotion": "relief",
        "energy": 0.5,
        "tempo": 95,
        "instruments": ["piano", "strings"],
    }
)
draft_id = uuid4()
confirmed_draft_id = uuid4()


with TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    revision_file = temporary_root / "database" / "local" / "revisions.json"

    from unittest.mock import patch

    with patch("ai_engine.creation.revision_store.REVISION_FILE", revision_file):
        # 没有 Draft 也可以保存和比较 Revision，模拟已确认作品的历史。
        save_revision(
            BlueprintRevision(
                draft_id=draft_id,
                version=1,
                blueprint=blueprint_v1,
            )
        )
        save_revision(
            BlueprintRevision(
                draft_id=draft_id,
                version=2,
                edit_instruction="节奏快一点，换成弦乐。",
                blueprint=blueprint_v2,
            )
        )
        save_revision(
            BlueprintRevision(
                draft_id=draft_id,
                version=3,
                edit_instruction="只记录相同内容。",
                blueprint=blueprint_v2,
            )
        )
        save_revision(
            BlueprintRevision(
                draft_id=confirmed_draft_id,
                version=1,
                blueprint=blueprint_v1,
            )
        )

        file_before_compare = revision_file.read_text(encoding="utf-8")
        differences = compare_blueprint_revisions(draft_id, 1, 2)

        # 只返回真正发生变化的字段，from/to 方向和参数顺序一致。
        assert differences == {
            "primary_emotion": {"from": "achievement", "to": "relief"},
            "energy": {"from": 0.4, "to": 0.5},
            "tempo": {"from": 85, "to": 95},
            "instruments": {
                "from": ["piano", "guitar"],
                "to": ["piano", "strings"],
            },
        }
        assert "texture" not in differences
        assert "valence" not in differences
        assert json.loads(json.dumps(differences)) == differences

        # 反向比较时 from/to 必须交换。
        reverse_differences = compare_blueprint_revisions(draft_id, 2, 1)
        assert reverse_differences["tempo"] == {"from": 95, "to": 85}
        assert reverse_differences["instruments"] == {
            "from": ["piano", "strings"],
            "to": ["piano", "guitar"],
        }

        # 相同版本、内容相同但版本不同的两个 Revision 都没有差异。
        assert compare_blueprint_revisions(draft_id, 2, 2) == {}
        assert compare_blueprint_revisions(draft_id, 2, 3) == {}

        # 返回结果和 Revision 不共享列表对象，比较过程也不会写入文件。
        differences["instruments"]["from"].append("drums")
        assert blueprint_v1.instruments == ["piano", "guitar"]
        assert revision_file.read_text(encoding="utf-8") == file_before_compare

        # 模拟已确认作品：只要 Revision 存在，就仍可比较。
        assert compare_blueprint_revisions(confirmed_draft_id, 1, 1) == {}

        # 不存在的版本、草稿 ID 和非法版本号必须明确拒绝。
        try:
            compare_blueprint_revisions(draft_id, 1, 99)
            raise AssertionError("不存在的版本应该被拒绝。")
        except ValueError:
            pass

        try:
            compare_blueprint_revisions(uuid4(), 1, 1)
            raise AssertionError("不存在的草稿 ID 应该被拒绝。")
        except ValueError:
            pass

        for invalid_version in [0, -1, True, "2"]:
            try:
                compare_blueprint_revisions(draft_id, invalid_version, 1)
                raise AssertionError("非法版本号应该被拒绝。")
            except ValueError:
                pass

        print("Revision Differences (V1 → V2):")
        print(format_record(compare_blueprint_revisions(draft_id, 1, 2)))

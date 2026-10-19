"""
测试 BlueprintRevision 数据结构。

只测试内存中的 Schema 创建和校验，
不调用 Ollama，也不读写任何 JSON 文件。
"""

import json
from datetime import timedelta
from pathlib import Path
import sys
from uuid import UUID

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation import BlueprintRevision, CreationDraft
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
    text="今天终于完成比赛了，虽然很累，但是感觉很值得。",
    emotion=emotion,
    blueprint=blueprint,
)


# 初始版本可以没有修改指令
first_revision = BlueprintRevision(
    draft_id=draft.id,
    version=1,
    blueprint=blueprint,
)

# 修改版本保存用户指令和新的完整 Blueprint
second_blueprint = MusicBlueprint(
    **{
        **blueprint.model_dump(),
        "tempo": 82,
        "texture": "soft",
    }
)
second_revision = BlueprintRevision(
    draft_id=draft.id,
    version=2,
    edit_instruction="节奏慢一点，整体温柔一些。",
    blueprint=second_blueprint,
)


# 自动生成字段、草稿关联和版本号均应正确
assert isinstance(first_revision.id, UUID)
assert first_revision.id != second_revision.id
assert first_revision.draft_id == draft.id
assert first_revision.version == 1
assert first_revision.edit_instruction is None
assert second_revision.version == 2
assert second_revision.edit_instruction == "节奏慢一点，整体温柔一些。"
assert first_revision.created_at.tzinfo is not None
assert first_revision.created_at.utcoffset() == timedelta(hours=8)

# Revision 保存的是独立快照，不会修改 Draft，也不会共享 Blueprint 对象
assert first_revision.blueprint == blueprint
assert first_revision.blueprint is not blueprint
assert draft.blueprint == blueprint
blueprint.tempo = 120
assert first_revision.blueprint.tempo == 108


# model_dump() 与 JSON 序列化都应正常工作
dumped_revision = second_revision.model_dump(mode="json")
assert isinstance(dumped_revision["id"], str)
assert isinstance(dumped_revision["draft_id"], str)
assert isinstance(dumped_revision["created_at"], str)
assert json.loads(second_revision.model_dump_json())["version"] == 2


# 非法版本号、空白修改要求和无效 Blueprint 都应被拒绝
invalid_cases = [
    {
        "draft_id": draft.id,
        "version": 0,
        "blueprint": second_blueprint,
    },
    {
        "draft_id": draft.id,
        "version": -1,
        "blueprint": second_blueprint,
    },
    {
        "draft_id": draft.id,
        "version": 2,
        "edit_instruction": "   ",
        "blueprint": second_blueprint,
    },
    {
        "draft_id": draft.id,
        "version": 2,
        "blueprint": {
            **second_blueprint.model_dump(),
            "energy": 1.2,
        },
    },
]

for invalid_case in invalid_cases:
    try:
        BlueprintRevision(**invalid_case)
        raise AssertionError("无效 Revision 数据应该被拒绝。")
    except ValidationError:
        pass


# 本测试只创建内存对象，不会写入 drafts.json 或 memories.json
print("Blueprint Revision:")
print(format_record(second_revision.model_dump(mode="json")))

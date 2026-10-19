"""
测试 CreationDraft 数据结构。

不调用 Ollama，
不读取或写入真实 memories.json，
只测试草稿创建与数据校验。
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
from ai_engine.creation import CreationDraft
from ai_engine.memory.schema import EmotionSnapshot
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


# 正常创建草稿，并验证系统自动生成的字段
draft = CreationDraft(
    text="今天终于完成比赛了，虽然很累，但是感觉很值得。",
    emotion=emotion,
    blueprint=blueprint,
)
second_draft = CreationDraft(
    text="晚上想为自己做一首安静的音乐。",
    emotion=emotion,
    blueprint=blueprint,
)

assert isinstance(draft.id, UUID)
assert draft.id != second_draft.id
assert draft.created_at.tzinfo is not None
assert draft.created_at.utcoffset() == timedelta(hours=8)
assert isinstance(draft.emotion, EmotionSnapshot)
assert draft.blueprint == blueprint


# model_dump() 与 JSON 序列化都应正常工作
dumped_draft = draft.model_dump(mode="json")
assert isinstance(dumped_draft["id"], str)
assert isinstance(dumped_draft["created_at"], str)
assert json.loads(draft.model_dump_json())["text"] == draft.text


# 空白 text、无效 emotion 与无效 Blueprint 都应被拒绝
invalid_cases = [
    {
        "text": "   ",
        "emotion": emotion,
        "blueprint": blueprint,
    },
    {
        "text": "缺少场景的情绪结果",
        "emotion": {
            "primary_emotion": "achievement",
            "secondary_emotions": ["fatigue"],
        },
        "blueprint": blueprint,
    },
    {
        "text": "无效 Blueprint",
        "emotion": emotion,
        "blueprint": {
            **blueprint.model_dump(),
            "energy": 1.2,
        },
    },
]

for invalid_case in invalid_cases:
    try:
        CreationDraft(**invalid_case)
        raise AssertionError("无效草稿数据应该被拒绝。")
    except ValidationError:
        pass


# 本测试只创建内存对象，不会调用 save_memory() 或写入 memories.json
print("CreationDraft:")
print(format_record(draft.model_dump(mode="json")))

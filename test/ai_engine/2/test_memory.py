"""
测试 MusicMemory 数据结构

不调用 LLM，
不连接数据库，
只测试 Memory 的创建与数据校验。
"""

from datetime import timedelta
from pathlib import Path
import sys
from uuid import UUID

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory import MusicMemory
from test.output_format import format_record


# 模拟情绪理解模块的输出
emotion = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "scene": "completed_competition",
}

# 构造一个已校验的 Music Blueprint
blueprint = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.8,
    valence=0.8,
    tempo=108,
    key="C Major",
    instruments=["piano", "guitar", "strings"],
    texture="warm",
    scene="celebration",
    progression="calm_to_rising",
)

# 创建一条用户音乐记忆
memory = MusicMemory(
    text="今天终于完成比赛了，虽然很累，但是感觉很值得。",
    emotion=emotion,
    blueprint=blueprint,
)

# 验证系统自动生成的字段
assert isinstance(memory.id, UUID)
assert memory.created_at.tzinfo is not None
assert memory.created_at.utcoffset() == timedelta(hours=8)
assert memory.emotion.primary_emotion == "achievement"
assert memory.blueprint.tempo == 108

# 构造一个 energy 超出范围的 Blueprint
invalid_blueprint = blueprint.model_dump()
invalid_blueprint["energy"] = 1.2

# 三种必须失败的数据情况
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
        "blueprint": invalid_blueprint,
    },
]

for invalid_case in invalid_cases:
    try:
        MusicMemory(**invalid_case)
    except ValidationError:
        # 能正确拦截无效数据即可
        pass
    else:
        raise AssertionError(f"无效数据没有被拦截：{invalid_case}")

# 使用统一格式输出最终结果
print("MusicMemory:")
print(format_record(memory.model_dump(mode="json")))

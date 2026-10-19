"""
测试带历史记忆参考的 Music Blueprint Generator。

使用 Mock 模拟 LLM 返回值，
不调用本地 Ollama。
"""

import json
from pathlib import Path
import sys
from unittest.mock import patch

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.generator import generate_blueprint
from ai_engine.blueprint.schema import MusicBlueprint


context = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "scene": "completed_project",
}

memory_context = """
相关历史记忆 1：
用户原话：比赛终于结束了，虽然很累，但我觉得很值得。
当时的音乐设计：tempo: 108，instruments: piano, strings。
"""

valid_data = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "energy": 0.8,
    "valence": 0.8,
    "tempo": 108,
    "key": "C Major",
    "instruments": ["piano", "strings"],
    "texture": "warm",
    "scene": "celebration",
    "progression": "calm_to_rising",
}

valid_response = json.dumps(valid_data, ensure_ascii=False)


def get_prompt(memory: str | None = None) -> tuple[MusicBlueprint, str]:
    """使用 Mock LLM 调用 Generator，并返回生成结果和实际 Prompt。"""
    with patch(
        "ai_engine.blueprint.generator.call_llm",
        return_value=valid_response,
    ) as mock_call_llm:
        if memory is None:
            blueprint = generate_blueprint(context)
        else:
            blueprint = generate_blueprint(context, memory_context=memory)

    prompt = mock_call_llm.call_args.args[0]
    return blueprint, prompt


# 不传 memory_context、空字符串和纯空白字符都应使用普通 Prompt
for empty_memory in [None, "", "   "]:
    blueprint, prompt = get_prompt(empty_memory)
    assert isinstance(blueprint, MusicBlueprint)
    assert "你还会收到一份历史记忆参考数据" not in prompt
    assert str(context) in prompt


# 有效历史记忆应使用带记忆的 Prompt，并正确注入两份上下文
blueprint, memory_prompt = get_prompt(memory_context)
assert isinstance(blueprint, MusicBlueprint)
assert "你还会收到一份历史记忆参考数据" in memory_prompt
assert str(context) in memory_prompt
assert memory_context.strip() in memory_prompt


# 非法 JSON 必须继续由原有 Parser 拦截
with patch(
    "ai_engine.blueprint.generator.call_llm",
    return_value="这不是 JSON",
):
    try:
        generate_blueprint(context)
        raise AssertionError("非法 JSON 应该被 Parser 拦截。")
    except ValueError:
        pass


# 不符合 MusicBlueprint Schema 的数据必须继续被 Pydantic 拦截
invalid_data = valid_data.copy()
invalid_data["energy"] = 1.2

with patch(
    "ai_engine.blueprint.generator.call_llm",
    return_value=json.dumps(invalid_data, ensure_ascii=False),
):
    try:
        generate_blueprint(context)
        raise AssertionError("无效 Blueprint 应该被 Pydantic 拦截。")
    except ValidationError:
        pass


print("Memory-aware Blueprint Generator tests passed.")

"""
测试 Music Blueprint 自然语言修改 Prompt。

只测试 Prompt 模板构建，
不调用 Ollama，也不修改草稿。
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.blueprint.progression import PROGRESSION_VALUES
from ai_engine.llm.prompts import (
    BLUEPRINT_EDIT_PROMPT,
    BLUEPRINT_PROMPT,
    MEMORY_AWARE_BLUEPRINT_PROMPT,
)


original_text = "今天终于完成比赛了，虽然很累，但是感觉很值得。"
current_blueprint = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.8,
    valence=0.7,
    tempo=115,
    key="C Major",
    instruments=["piano", "guitar"],
    texture="bright",
    scene="celebration",
    progression="calm_to_rising",
).model_dump_json(indent=2)
edit_instruction = "能不能再温柔一点，速度慢一些，钢琴保留，但是不要吉他了。"


# 三个输入都应正确注入，JSON 示例的大括号不会导致 format() 异常
edit_prompt = BLUEPRINT_EDIT_PROMPT.format(
    original_text=original_text,
    current_blueprint=current_blueprint,
    edit_instruction=edit_instruction,
)
assert original_text in edit_prompt
assert current_blueprint in edit_prompt
assert edit_instruction in edit_prompt
assert "{original_text}" not in edit_prompt
assert "{current_blueprint}" not in edit_prompt
assert "{edit_instruction}" not in edit_prompt


# Prompt 必须限制无关修改，并要求完整 JSON 输出
assert "未明确要求修改的字段原则上保持原有值" in edit_prompt
assert "不能无故大幅改变整体音乐设计" in edit_prompt
assert "只能输出完整的 MusicBlueprint JSON 对象" in edit_prompt
assert "不要只输出发生变化的字段" in edit_prompt
assert "不要声称已经修改或生成了真实音频" in edit_prompt
for progression in PROGRESSION_VALUES:
    assert f"- {progression}:" in edit_prompt


# 原有两个 Blueprint Prompt 仍可正常构建
normal_prompt = BLUEPRINT_PROMPT.format(context={"primary_emotion": "achievement"})
memory_aware_prompt = MEMORY_AWARE_BLUEPRINT_PROMPT.format(
    context={"primary_emotion": "achievement"},
    memory_context="",
)
assert "{context}" not in normal_prompt
assert "{memory_context}" not in memory_aware_prompt


print("Blueprint Edit Prompt built successfully.")

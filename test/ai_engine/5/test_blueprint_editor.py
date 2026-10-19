"""
测试 AI Music Blueprint 修改器。

使用 Mock 模拟 LLM 返回值，
不调用 Ollama，不修改或保存 CreationDraft。
"""

import json
from pathlib import Path
import sys
from unittest.mock import patch

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint import MusicBlueprint, edit_blueprint


original_text = "今天比赛结束了，虽然很累但很满足。"
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
)
edit_instruction = "整体再温柔一点，节奏慢一些，钢琴保留，不要吉他。"
edited_data = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "energy": 0.4,
    "valence": 0.7,
    "tempo": 85,
    "key": "C Major",
    "instruments": ["piano", "strings"],
    "texture": "soft",
    "scene": "celebration",
    "progression": "calm_to_rising",
}
valid_response = json.dumps(edited_data, ensure_ascii=False)
original_blueprint_data = current_blueprint.model_dump()
current_blueprint_json = current_blueprint.model_dump_json(indent=2)


# 合法 LLM JSON 应生成新的、经过 Schema 校验的 MusicBlueprint
with (
    patch(
        "ai_engine.blueprint.editor.call_llm",
        return_value=valid_response,
    ) as mock_call_llm,
    patch("ai_engine.creation.store.save_draft") as mock_save_draft,
    patch("ai_engine.creation.manager.update_draft_blueprint") as mock_update_draft,
    patch("ai_engine.memory.manager.commit_memory") as mock_commit_memory,
):
    edited_blueprint = edit_blueprint(
        original_text,
        current_blueprint,
        edit_instruction,
    )

    prompt = mock_call_llm.call_args.args[0]
    assert isinstance(edited_blueprint, MusicBlueprint)
    assert edited_blueprint == MusicBlueprint.model_validate(edited_data)
    assert original_text in prompt
    assert current_blueprint_json in prompt
    assert edit_instruction in prompt
    assert current_blueprint.model_dump() == original_blueprint_data
    mock_save_draft.assert_not_called()
    mock_update_draft.assert_not_called()
    mock_commit_memory.assert_not_called()


# 空输入应在调用 LLM 前被拒绝
with patch("ai_engine.blueprint.editor.call_llm") as mock_call_llm:
    for invalid_original_text, invalid_instruction in [
        ("", edit_instruction),
        ("   ", edit_instruction),
        (original_text, ""),
        (original_text, "   "),
    ]:
        try:
            edit_blueprint(
                invalid_original_text,
                current_blueprint,
                invalid_instruction,
            )
            raise AssertionError("空输入应该被拒绝。")
        except ValueError:
            pass

    mock_call_llm.assert_not_called()


# 非法 JSON 必须继续由 Parser 拦截
with patch(
    "ai_engine.blueprint.editor.call_llm",
    return_value="这不是 JSON",
):
    try:
        edit_blueprint(original_text, current_blueprint, edit_instruction)
        raise AssertionError("非法 JSON 应该被 Parser 拦截。")
    except ValueError:
        pass


# 缺失字段和非法数值必须继续由 Pydantic 拦截
invalid_responses = [
    {
        key: value
        for key, value in edited_data.items()
        if key != "tempo"
    },
    {
        **edited_data,
        "energy": 1.2,
    },
]

for invalid_data in invalid_responses:
    with patch(
        "ai_engine.blueprint.editor.call_llm",
        return_value=json.dumps(invalid_data, ensure_ascii=False),
    ):
        try:
            edit_blueprint(original_text, current_blueprint, edit_instruction)
            raise AssertionError("无效 Blueprint 应该被 Pydantic 拦截。")
        except ValidationError:
            pass


print("Blueprint Editor tests passed.")

import json
from types import SimpleNamespace

import pytest

from music_companion.revision_suggestions import generate_revision_suggestions


def test_suggestions_use_current_interpretation_and_retry_invalid_output():
    narrative = SimpleNamespace(model_dump=lambda **_: {"listening_guide": ["结尾逐渐变弱"]})
    interpretation = SimpleNamespace(narrative=narrative)
    prompts = []
    suggestions = [{"title": f"方向{i}", "rationale": "结尾逐渐变弱，可以延长余韵让收束更自然。", "modification_text": "保持整体情绪，让音乐的背景音色缓慢展开。", "scope": "global"} for i in range(3)]

    def llm(prompt):
        prompts.append(prompt)
        return "invalid" if len(prompts) == 1 else json.dumps({"suggestions": suggestions}, ensure_ascii=False)

    result = generate_revision_suggestions(interpretation, seen_titles=["旧建议"], llm_call=llm)
    assert len(result.suggestions) == 3
    assert len(prompts) == 2
    assert "结尾逐渐变弱" in prompts[0]
    assert "旧建议" in prompts[0]


def test_unavailable_model_does_not_return_generic_fallback():
    interpretation = SimpleNamespace(narrative=SimpleNamespace(model_dump=lambda **_: {}))
    with pytest.raises(RuntimeError, match="无法根据当前音乐解读生成建议"):
        generate_revision_suggestions(interpretation, llm_call=lambda _: "invalid")

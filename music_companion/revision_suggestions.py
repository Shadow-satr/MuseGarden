"""基于已验证音乐解读生成下一版修改建议。"""

from __future__ import annotations

import json
from typing import Callable, Literal, Sequence

from pydantic import BaseModel, Field

from ai_engine.llm.client import call_llm
from ai_engine.llm.parser import parse_json_response
from music_companion.schema import MusicInterpretationResult


class RevisionSuggestion(BaseModel):
    title: str = Field(min_length=2, max_length=40)
    rationale: str = Field(min_length=12, max_length=180)
    modification_text: str = Field(min_length=12, max_length=300)
    scope: Literal["global", "local"]


class RevisionSuggestionSet(BaseModel):
    suggestions: tuple[RevisionSuggestion, ...] = Field(min_length=3, max_length=3)


def generate_revision_suggestions(
    interpretation: MusicInterpretationResult,
    *,
    seen_titles: Sequence[str] = (),
    llm_call: Callable[[str], str] = call_llm,
) -> RevisionSuggestionSet:
    """生成三条不同的、可直接填入修改框的建议。"""
    narrative = interpretation.narrative.model_dump(mode="json")
    prompt = f"""
你是音乐制作顾问。请针对以下这首音乐的解读，生成恰好三条不同的修改建议。
每条都要依据解读中具体的整体听感或段落细节说明理由，并给出相应的可执行修改。
先识别这首音乐的特点，结合当前音乐自由选择适合的整体或局部修改方向。
每组三条中至少一条针对整首音乐，修改指令应明确写出“整体”或“全曲”，并标记 scope 为 global。
只针对某一段的建议标记 scope 为 local，其余方向可自由选择。
不要套用固定模板，不要默认有高潮、鼓点或某种乐器。证据不确定时使用“可以尝试”，不要当作事实。
修改指令需要具体描述希望改变的音乐效果，并尽量说明需要保留的现有特点。
避免与以下已展示标题重复：{json.dumps(list(seen_titles), ensure_ascii=False)}。
只输出 JSON：{{"suggestions":[{{"title":"简短方向","rationale":"结合本曲解读的理由","modification_text":"可直接用于修改音乐的完整指令","scope":"global 或 local"}}]}}。

当前音乐解读：
{json.dumps(narrative, ensure_ascii=False)}
""".strip()
    for attempt in range(2):
        try:
            retry = "\n请严格返回三条不同建议，至少一条 scope 为 global 且修改指令包含“整体”或“全曲”。" if attempt else ""
            result = RevisionSuggestionSet.model_validate(parse_json_response(llm_call(prompt + retry)))
            titles = [item.title.strip() for item in result.suggestions]
            if len(set(titles)) != 3 or set(titles) & set(seen_titles):
                raise ValueError("建议标题重复")
            if not any(
                item.scope == "global" and ("整体" in item.modification_text or "全曲" in item.modification_text)
                for item in result.suggestions
            ):
                raise ValueError("缺少针对整首音乐的建议")
            return result
        except Exception as error:
            if attempt == 1:
                raise RuntimeError("无法根据当前音乐解读生成建议，请重试") from error
    raise RuntimeError("无法根据当前音乐解读生成建议，请重试")

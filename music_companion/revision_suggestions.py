"""基于已验证音乐解读生成下一版修改建议。"""

from __future__ import annotations

import json
from typing import Callable, Sequence

from pydantic import BaseModel, Field

from ai_engine.llm.client import call_llm
from ai_engine.llm.parser import parse_json_response
from music_companion.schema import MusicInterpretationResult


class RevisionSuggestion(BaseModel):
    title: str = Field(min_length=2, max_length=40)
    rationale: str = Field(min_length=12, max_length=180)
    modification_text: str = Field(min_length=12, max_length=300)


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
你是音乐制作顾问。根据下方已经校验过的音乐解读，提出恰好 3 条中文修改建议。
目标是让下一版音乐更丰富、更完整，优先考虑：旋律发展、编配层次、段落衔接或结尾收束。
三条必须覆盖不同方向，不能只建议加快速度或增加鼓点；不把未确认的乐器或模型线索写成事实。
避免与已展示标题重复：{json.dumps(list(seen_titles), ensure_ascii=False)}。
只返回 JSON：{{"suggestions":[{{"title":"...","rationale":"...","modification_text":"可直接用于修改音乐的完整指令"}}]}}。

已验证解读：
{json.dumps(narrative, ensure_ascii=False)}
""".strip()
    try:
        result = RevisionSuggestionSet.model_validate(parse_json_response(llm_call(prompt)))
        titles = [item.title for item in result.suggestions]
        if len(set(titles)) != 3 or set(titles) & set(seen_titles):
            raise ValueError("建议标题重复")
        return result
    except Exception:
        return _fallback_suggestions(seen_titles)


def _fallback_suggestions(seen_titles: Sequence[str]) -> RevisionSuggestionSet:
    """本地小模型未遵循契约时仍给出三条可用、方向不同的建议。"""
    candidates = (
        RevisionSuggestion(
            title="让旋律更有回应",
            rationale="当前版本已有清晰的旋律前景，可以用短句回应让主线更有记忆点。",
            modification_text="保留现有整体速度与情绪，让中段主旋律加入更明显的上下行与回应式短句，并避免增加过密的鼓点。",
        ),
        RevisionSuggestion(
            title="逐步展开背景层次",
            rationale="让背景音色在中段慢慢加入，能让段落推进更丰富而不拥挤。",
            modification_text="保留主旋律清晰度，在中段逐步增加弦乐或氛围背景的持续支撑，并让低频层次更平稳地进入。",
        ),
        RevisionSuggestion(
            title="让结尾收束更完整",
            rationale="在高潮之后保留短暂余韵，可以让作品结束得更自然。",
            modification_text="让结尾在主旋律结束后保留一小段较轻的背景音色和延续感，再自然淡出，避免能量突然回落。",
        ),
        RevisionSuggestion(
            title="增强段落之间的连接",
            rationale="通过渐进的编配变化连接开头和中段，能让短篇结构更完整。",
            modification_text="在开头进入中段前加入渐进的音色叠加与旋律延续，让能量抬升更连贯，同时保持主旋律在前景。",
        ),
    )
    seen = set(seen_titles)
    unseen = [item for item in candidates if item.title not in seen]
    extra_index = 1
    while len(unseen) < 3:
        title = f"探索新的层次方向 {extra_index}"
        extra_index += 1
        if title in seen:
            continue
        unseen.append(RevisionSuggestion(
            title=title,
            rationale="尝试一个尚未展示过的编配方向，为下一版保留新的听感选择。",
            modification_text="保持主旋律清晰，尝试用更渐进的背景音色变化连接各段，并避免让单一声部长期占据全部前景。",
        ))
    chosen = unseen[:3]
    return RevisionSuggestionSet(suggestions=tuple(chosen))

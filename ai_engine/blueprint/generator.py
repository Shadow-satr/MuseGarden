"""根据语义理解结果生成经过校验的 MusicBlueprint。"""

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.llm.client import call_llm
from ai_engine.llm.parser import parse_json_response
from ai_engine.llm.prompts.blueprint import (
    BLUEPRINT_PROMPT,
    MEMORY_AWARE_BLUEPRINT_PROMPT,
)


def generate_blueprint(
    context: dict,
    memory_context: str = "",
) -> MusicBlueprint:
    """有历史记忆时使用对应 Prompt；否则使用普通 Prompt。"""
    if memory_context.strip():
        prompt = MEMORY_AWARE_BLUEPRINT_PROMPT.format(
            context=context,
            memory_context=memory_context,
        )
    else:
        prompt = BLUEPRINT_PROMPT.format(context=context)

    return MusicBlueprint.model_validate(parse_json_response(call_llm(prompt)))

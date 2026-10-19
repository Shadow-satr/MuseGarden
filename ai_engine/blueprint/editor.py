"""
Music Blueprint 修改模块。

根据用户自然语言修改要求，
在当前 MusicBlueprint 基础上生成新的候选 Blueprint。
"""

from ai_engine.llm.client import call_llm
from ai_engine.llm.parser import parse_json_response
from ai_engine.llm.prompts.blueprint_edit import BLUEPRINT_EDIT_PROMPT

from .schema import MusicBlueprint


def edit_blueprint(
    original_text: str,
    current_blueprint: MusicBlueprint,
    edit_instruction: str,
) -> MusicBlueprint:
    """
    根据用户修改要求生成新的 MusicBlueprint。

    不修改原始 current_blueprint，
    只返回经过完整校验的新对象。
    """
    if not original_text or not original_text.strip():
        raise ValueError("用户最初输入不能为空。")

    if not edit_instruction or not edit_instruction.strip():
        raise ValueError("用户修改要求不能为空。")

    if not isinstance(current_blueprint, MusicBlueprint):
        raise TypeError("current_blueprint 必须是 MusicBlueprint。")

    prompt = BLUEPRINT_EDIT_PROMPT.format(
        original_text=original_text,
        current_blueprint=current_blueprint.model_dump_json(indent=2),
        edit_instruction=edit_instruction,
    )
    return MusicBlueprint.model_validate(parse_json_response(call_llm(prompt)))

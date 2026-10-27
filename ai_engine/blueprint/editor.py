"""
Music Blueprint 修改模块。

根据用户自然语言修改要求，
在当前 MusicBlueprint 基础上生成新的候选 Blueprint。
"""

from ai_engine.llm.client import call_llm
from ai_engine.llm.parser import parse_json_response
from ai_engine.llm.prompts.blueprint_edit import BLUEPRINT_EDIT_PROMPT

from .schema import MusicBlueprint


def _restore_blank_identity_fields(
    candidate: object,
    current_blueprint: MusicBlueprint,
) -> object:
    """保留模型未实际修改、却以空字符串返回的基础音乐字段。

    修改音乐时，LLM 偶尔会保留完整字段名却把 key、texture 等未涉及字段填成空字符串。
    这不是用户请求的修改，也无法被 MusicGenerationSpec 使用；用当前版本的同名字段补回。
    缺失字段、错误类型和数值越界仍交给 MusicBlueprint 正常拒绝。
    """
    if not isinstance(candidate, dict):
        return candidate
    restored = dict(candidate)
    for field in ("primary_emotion", "key", "texture", "scene"):
        value = restored.get(field)
        if isinstance(value, str) and not value.strip():
            restored[field] = getattr(current_blueprint, field)
    return restored


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
    candidate = parse_json_response(call_llm(prompt))
    return MusicBlueprint.model_validate(
        _restore_blank_identity_fields(candidate, current_blueprint),
    )

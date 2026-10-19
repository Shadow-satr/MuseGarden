"""
LLM Prompt 模板模块。
"""

from .blueprint import BLUEPRINT_PROMPT, MEMORY_AWARE_BLUEPRINT_PROMPT
from .blueprint_edit import BLUEPRINT_EDIT_PROMPT
from .emotion import EMOTION_PROMPT

# 当前已实现的 Prompt 模板
__all__ = [
    "BLUEPRINT_PROMPT",
    "BLUEPRINT_EDIT_PROMPT",
    "EMOTION_PROMPT",
    "MEMORY_AWARE_BLUEPRINT_PROMPT",
]

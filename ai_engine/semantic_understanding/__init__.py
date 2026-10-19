"""
用户语义理解模块。
"""

from .emotion import analyze_emotion

# 当前语义理解模块对外提供的能力
__all__ = ["analyze_emotion"]

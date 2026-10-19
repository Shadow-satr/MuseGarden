"""
Music Blueprint 数据结构与生成逻辑模块。
"""

from .editor import edit_blueprint
from .generator import generate_blueprint
from .progression import PROGRESSION_VALUES, Progression
from .schema import MusicBlueprint

# Blueprint 模块对外提供的数据结构和生成方法
__all__ = [
    "MusicBlueprint",
    "Progression",
    "PROGRESSION_VALUES",
    "edit_blueprint",
    "generate_blueprint",
]

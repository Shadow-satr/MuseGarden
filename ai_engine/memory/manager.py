"""
用户音乐记忆提交服务。

负责在外部明确确认作品后，
创建并保存一条完整的 MusicMemory。
"""

from ai_engine.blueprint.schema import MusicBlueprint
from uuid import UUID

from .schema import EmotionSnapshot, MusicMemory
from .store import save_memory


def commit_memory(
    text: str,
    emotion: EmotionSnapshot | dict,
    blueprint: MusicBlueprint,
    memory_id: UUID | None = None,
) -> MusicMemory:
    """
    创建并正式保存一条用户音乐记忆。

    调用方应仅在用户明确确认作品后调用此函数。
    """
    memory_data = {
        "text": text,
        "emotion": emotion,
        "blueprint": blueprint,
    }

    if memory_id is not None:
        memory_data["id"] = memory_id

    memory = MusicMemory(
        **memory_data,
    )

    save_memory(memory)

    return memory

"""
用户音乐记忆查询模块

负责从已保存的 Memory 中查找历史记录。
支持字段、关键词和 Embedding 语义检索。
不负责保存数据。
"""

from dataclasses import dataclass
from pathlib import Path

from .embedding import embed_text
from .schema import MusicMemory
from .similarity import cosine_similarity
from .store import load_memories


@dataclass(frozen=True)
class SemanticSearchResult:
    """一条语义检索结果，包含历史记忆与对应相似度。"""

    memory: MusicMemory
    similarity: float


def find_by_emotion(
    primary_emotion: str,
    file_path: Path | None = None,
) -> list[MusicMemory]:
    """
    根据主要情绪查找历史记忆。

    字符串匹配忽略大小写。
    """
    target_emotion = primary_emotion.lower()
    memories = load_memories(file_path)

    return [
        memory
        for memory in memories
        if memory.emotion.primary_emotion.lower() == target_emotion
    ]


def find_by_scene(
    scene: str,
    file_path: Path | None = None,
) -> list[MusicMemory]:
    """
    根据用户经历发生的场景查找历史记忆。

    查询的是 emotion.scene，字符串匹配忽略大小写。
    """
    target_scene = scene.lower()
    memories = load_memories(file_path)

    return [
        memory
        for memory in memories
        if memory.emotion.scene.lower() == target_scene
    ]


def search_by_text(
    keyword: str,
    file_path: Path | None = None,
) -> list[MusicMemory]:
    """
    根据用户原始输入中的关键词查找历史记忆。

    使用简单的关键词包含匹配，字符串匹配忽略大小写。
    """
    target_keyword = keyword.lower()
    memories = load_memories(file_path)

    return [
        memory
        for memory in memories
        if target_keyword in memory.text.lower()
    ]


def semantic_search(
    query: str,
    top_k: int = 3,
    file_path: Path | None = None,
) -> list[SemanticSearchResult]:
    """
    根据文本语义查找最相近的历史记忆。

    每次查询都会现场生成 query 和每条 Memory 的 Embedding。
    file_path 仅用于测试时指定临时的 memories.json 路径。
    """
    if not query or not query.strip():
        raise ValueError("语义查询文本不能为空。")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k 必须是大于 0 的整数。")

    memories = load_memories(file_path)

    if not memories:
        return []

    query_embedding = embed_text(query)
    results: list[SemanticSearchResult] = []

    for memory in memories:
        memory_embedding = embed_text(memory.text)
        similarity = cosine_similarity(query_embedding, memory_embedding)
        results.append(
            SemanticSearchResult(
                memory=memory,
                similarity=similarity,
            )
        )

    results.sort(key=lambda result: result.similarity, reverse=True)

    return results[:top_k]

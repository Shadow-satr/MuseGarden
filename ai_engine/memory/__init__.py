"""
用户音乐记忆模块
"""

from .schema import EmotionSnapshot, MusicMemory
from .context_builder import build_memory_context
from .embedding import embed_text
from .manager import commit_memory
from .retriever import (
    SemanticSearchResult,
    find_by_emotion,
    find_by_scene,
    search_by_text,
    semantic_search,
)
from .similarity import cosine_similarity
from .store import load_memories, save_memory

# 方便其他模块直接导入 Memory 数据结构、存储和查询方法
__all__ = [
    "EmotionSnapshot",
    "MusicMemory",
    "SemanticSearchResult",
    "build_memory_context",
    "commit_memory",
    "cosine_similarity",
    "embed_text",
    "find_by_emotion",
    "find_by_scene",
    "load_memories",
    "save_memory",
    "search_by_text",
    "semantic_search",
]

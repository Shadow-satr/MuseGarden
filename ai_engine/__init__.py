"""
MuseGarden AI 核心引擎。
"""

from .blueprint import MusicBlueprint, edit_blueprint, generate_blueprint
from .creation import (
    CreationDraft,
    BlueprintRevision,
    compare_blueprint_revisions,
    confirm_draft,
    delete_draft,
    edit_creation_draft,
    load_drafts,
    load_revisions,
    replace_draft,
    restore_blueprint_revision,
    save_draft,
    save_revision,
    start_creation,
    update_draft_blueprint,
)
from .memory import (
    MusicMemory,
    SemanticSearchResult,
    build_memory_context,
    commit_memory,
    cosine_similarity,
    embed_text,
    find_by_emotion,
    find_by_scene,
    load_memories,
    save_memory,
    search_by_text,
    semantic_search,
)
from .semantic_understanding import analyze_emotion
from .pipeline import run_creation_pipeline, run_music_pipeline

# AI 引擎当前对外提供的核心能力
__all__ = [
    "MusicBlueprint",
    "CreationDraft",
    "BlueprintRevision",
    "MusicMemory",
    "SemanticSearchResult",
    "analyze_emotion",
    "build_memory_context",
    "commit_memory",
    "compare_blueprint_revisions",
    "confirm_draft",
    "cosine_similarity",
    "delete_draft",
    "embed_text",
    "edit_blueprint",
    "edit_creation_draft",
    "find_by_emotion",
    "find_by_scene",
    "generate_blueprint",
    "load_memories",
    "load_drafts",
    "load_revisions",
    "replace_draft",
    "restore_blueprint_revision",
    "run_music_pipeline",
    "run_creation_pipeline",
    "save_memory",
    "save_draft",
    "save_revision",
    "start_creation",
    "search_by_text",
    "semantic_search",
    "update_draft_blueprint",
]

"""
音乐生成与处理引擎模块。
"""

from music_engine.adapter import blueprint_to_generation_spec
from music_engine.audio_store import AudioStore
from music_engine.final_creation import FinalCreation, FinalCreationStore
from music_engine.finalization import CreationFinalizationService
from music_engine.service import MusicGenerationService
from music_engine.version_service import MusicVersionService
from music_engine.workspace import MusicWorkspaceService
from music_engine.schema import (
    AceStepGenerationResult,
    AudioArtifact,
    MusicConfirmationBundle,
    MusicGenerationSpec,
)

__all__ = [
    "AceStepGenerationResult",
    "AudioStore",
    "AudioArtifact",
    "CreationFinalizationService",
    "FinalCreation",
    "FinalCreationStore",
    "MusicConfirmationBundle",
    "MusicGenerationSpec",
    "MusicGenerationService",
    "MusicVersionService",
    "MusicWorkspaceService",
    "blueprint_to_generation_spec",
]

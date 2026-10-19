"""
测试 CreationDraft 生成 Pipeline。

使用 Mock 模拟情绪理解、记忆检索与 Blueprint 生成，
不调用 Ollama，也不保存真实 Memory。
"""

from datetime import timedelta
from pathlib import Path
import sys
from unittest.mock import patch
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation import CreationDraft
from ai_engine.pipeline import run_creation_pipeline, run_music_pipeline


text = "今天终于完成比赛了，虽然很累但是很满足。"
emotion_result = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "scene": "completed_competition",
}
search_results = [object()]
memory_context = "相关历史记忆 1：比赛结束后感到满足。"
blueprint = MusicBlueprint(
    primary_emotion="achievement",
    secondary_emotions=["fatigue"],
    energy=0.8,
    valence=0.8,
    tempo=108,
    key="C Major",
    instruments=["piano", "strings"],
    texture="warm",
    scene="celebration",
    progression="calm_to_rising",
)


# 启用 Memory 时，应使用一次完整生成流程并返回 CreationDraft
with (
    patch("ai_engine.pipeline.analyze_emotion", return_value=emotion_result) as mock_emotion,
    patch("ai_engine.pipeline.semantic_search", return_value=search_results) as mock_search,
    patch("ai_engine.pipeline.build_memory_context", return_value=memory_context) as mock_builder,
    patch("ai_engine.pipeline.generate_blueprint", return_value=blueprint) as mock_generator,
    patch("ai_engine.memory.manager.commit_memory") as mock_commit_memory,
    patch("ai_engine.memory.manager.save_memory") as mock_save_memory,
):
    draft = run_creation_pipeline(text, use_memory=True, top_k=2)

    assert isinstance(draft, CreationDraft)
    assert draft.text == text
    assert draft.emotion.model_dump() == emotion_result
    assert draft.blueprint == blueprint
    assert isinstance(draft.id, UUID)
    assert draft.created_at.utcoffset() == timedelta(hours=8)
    mock_emotion.assert_called_once_with(text)
    mock_search.assert_called_once_with(text, top_k=2)
    mock_builder.assert_called_once_with(search_results)
    mock_generator.assert_called_once_with(
        context=emotion_result,
        memory_context=memory_context,
    )
    mock_commit_memory.assert_not_called()
    mock_save_memory.assert_not_called()


# 关闭 Memory 时，应跳过检索和上下文构建
with (
    patch("ai_engine.pipeline.analyze_emotion", return_value=emotion_result),
    patch("ai_engine.pipeline.semantic_search") as mock_search,
    patch("ai_engine.pipeline.build_memory_context") as mock_builder,
    patch("ai_engine.pipeline.generate_blueprint", return_value=blueprint) as mock_generator,
):
    draft = run_creation_pipeline(text, use_memory=False)

    assert isinstance(draft, CreationDraft)
    mock_search.assert_not_called()
    mock_builder.assert_not_called()
    mock_generator.assert_called_once_with(
        context=emotion_result,
        memory_context="",
    )


# 历史 Memory 为空时，仍应生成普通 CreationDraft
with (
    patch("ai_engine.pipeline.analyze_emotion", return_value=emotion_result) as mock_emotion,
    patch("ai_engine.pipeline.semantic_search", return_value=[]),
    patch("ai_engine.pipeline.build_memory_context") as mock_builder,
    patch("ai_engine.pipeline.generate_blueprint", return_value=blueprint),
):
    draft = run_creation_pipeline(text, use_memory=True)

    assert isinstance(draft, CreationDraft)
    mock_emotion.assert_called_once_with(text)
    mock_builder.assert_not_called()


# 原有接口必须仍然返回 MusicBlueprint
with (
    patch("ai_engine.pipeline.analyze_emotion", return_value=emotion_result),
    patch("ai_engine.pipeline.generate_blueprint", return_value=blueprint),
):
    old_result = run_music_pipeline(text, use_memory=False)

    assert isinstance(old_result, MusicBlueprint)


print("Creation Draft Pipeline tests passed.")

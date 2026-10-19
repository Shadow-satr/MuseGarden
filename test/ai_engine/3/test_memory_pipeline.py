"""
测试带历史记忆辅助的音乐设计 Pipeline。

使用 Mock 模拟已有模块，
不调用 Ollama，不读取或写入真实 Memory。
"""

from pathlib import Path
import sys
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.pipeline import run_music_pipeline


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


# 启用 Memory 时，应完成检索、上下文构建和带上下文的 Blueprint 生成
with (
    patch("ai_engine.pipeline.analyze_emotion", return_value=emotion_result) as mock_emotion,
    patch("ai_engine.pipeline.semantic_search", return_value=search_results) as mock_search,
    patch("ai_engine.pipeline.build_memory_context", return_value=memory_context) as mock_builder,
    patch("ai_engine.pipeline.generate_blueprint", return_value=blueprint) as mock_generator,
):
    result = run_music_pipeline(text, use_memory=True, top_k=2)

    assert isinstance(result, MusicBlueprint)
    mock_emotion.assert_called_once_with(text)
    mock_search.assert_called_once_with(text, top_k=2)
    mock_builder.assert_called_once_with(search_results)
    mock_generator.assert_called_once_with(
        context=emotion_result,
        memory_context=memory_context,
    )


# 关闭 Memory 时，应跳过检索和上下文构建
with (
    patch("ai_engine.pipeline.analyze_emotion", return_value=emotion_result),
    patch("ai_engine.pipeline.semantic_search") as mock_search,
    patch("ai_engine.pipeline.build_memory_context") as mock_builder,
    patch("ai_engine.pipeline.generate_blueprint", return_value=blueprint) as mock_generator,
):
    result = run_music_pipeline(text, use_memory=False)

    assert isinstance(result, MusicBlueprint)
    mock_search.assert_not_called()
    mock_builder.assert_not_called()
    mock_generator.assert_called_once_with(
        context=emotion_result,
        memory_context="",
    )


# 历史 Memory 为空时，应跳过 Context Builder 并使用普通生成
with (
    patch("ai_engine.pipeline.analyze_emotion", return_value=emotion_result),
    patch("ai_engine.pipeline.semantic_search", return_value=[]) as mock_search,
    patch("ai_engine.pipeline.build_memory_context") as mock_builder,
    patch("ai_engine.pipeline.generate_blueprint", return_value=blueprint) as mock_generator,
):
    result = run_music_pipeline(text, use_memory=True, top_k=5)

    assert isinstance(result, MusicBlueprint)
    mock_search.assert_called_once_with(text, top_k=5)
    mock_builder.assert_not_called()
    mock_generator.assert_called_once_with(
        context=emotion_result,
        memory_context="",
    )


# 空文本和非法 top_k 都应在调用其他模块前被拒绝
invalid_inputs = [
    ("", True, 3),
    ("   ", True, 3),
    (text, True, 0),
    (text, True, -1),
]

for invalid_text, use_memory, invalid_top_k in invalid_inputs:
    try:
        run_music_pipeline(
            invalid_text,
            use_memory=use_memory,
            top_k=invalid_top_k,
        )
        raise AssertionError("非法 Pipeline 输入应该被拒绝。")
    except ValueError:
        pass


print("Memory-assisted Music Pipeline tests passed.")

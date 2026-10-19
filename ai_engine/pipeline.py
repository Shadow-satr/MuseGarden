"""
MuseGarden 音乐设计 Pipeline。

负责调度情绪理解、历史记忆检索、上下文构建和 Blueprint 生成。
不负责保存 Memory、生成音频或生成花朵。
"""

from ai_engine.blueprint.generator import generate_blueprint
from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import CreationDraft
from ai_engine.memory import build_memory_context, semantic_search
from ai_engine.semantic_understanding.emotion import analyze_emotion


def run_music_pipeline(
    text: str,
    use_memory: bool = True,
    top_k: int = 3,
) -> MusicBlueprint:
    """
    根据用户输入生成 Music Blueprint。

    use_memory 为 True 时，会检索历史记忆并构建辅助参考文本。
    """
    _, blueprint = _run_blueprint_generation(
        text=text,
        use_memory=use_memory,
        top_k=top_k,
    )

    return blueprint


def run_creation_pipeline(
    text: str,
    use_memory: bool = True,
    top_k: int = 3,
) -> CreationDraft:
    """
    根据用户输入生成完整的 CreationDraft。

    草稿只存在于当前程序中，不会自动保存为 MusicMemory。
    """
    emotion_result, blueprint = _run_blueprint_generation(
        text=text,
        use_memory=use_memory,
        top_k=top_k,
    )

    return CreationDraft(
        text=text,
        emotion=emotion_result,
        blueprint=blueprint,
    )


def _run_blueprint_generation(
    text: str,
    use_memory: bool,
    top_k: int,
) -> tuple[dict, MusicBlueprint]:
    """执行两个公开 Pipeline 共用的 Blueprint 生成流程。"""
    if not text or not text.strip():
        raise ValueError("用户输入文本不能为空。")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k 必须是大于 0 的整数。")

    emotion_result = analyze_emotion(text)
    memory_context = ""

    if use_memory:
        search_results = semantic_search(text, top_k=top_k)

        if search_results:
            memory_context = build_memory_context(search_results)

    blueprint = generate_blueprint(
        context=emotion_result,
        memory_context=memory_context,
    )

    return emotion_result, blueprint

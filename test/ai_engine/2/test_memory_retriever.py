"""
测试 MusicMemory 基础查询功能

不调用 LLM，
不写入真实 memories.json，
只测试字段和关键词查询。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory import (
    MusicMemory,
    find_by_emotion,
    find_by_scene,
    save_memory,
    search_by_text,
)
from test.output_format import format_record


def create_memory(
    text: str,
    primary_emotion: str,
    scene: str,
) -> MusicMemory:
    """创建测试使用的 MusicMemory。"""
    return MusicMemory(
        text=text,
        emotion={
            "primary_emotion": primary_emotion,
            "secondary_emotions": [],
            "scene": scene,
        },
        blueprint=MusicBlueprint(
            primary_emotion=primary_emotion,
            secondary_emotions=[],
            energy=0.5,
            valence=0.6,
            tempo=90,
            key="C Major",
            instruments=["piano"],
            texture="soft",
            scene="home",
            progression="steady",
        ),
    )


competition_memory = create_memory(
    "今天的 Competition 终于结束了，虽然很累，但是感觉很值得。",
    "achievement",
    "competition_finished",
)

walk_memory = create_memory(
    "晚上一个人在操场散步，感觉很平静。",
    "calm",
    "late_night",
)


# 临时目录会在测试结束后自动删除
with TemporaryDirectory() as temporary_directory:
    memory_file = Path(temporary_directory) / "database" / "local" / "memories.json"

    # 保存两条不同的测试记忆
    save_memory(competition_memory, memory_file)
    save_memory(walk_memory, memory_file)

    # 主要情绪查询，验证大小写不影响结果
    emotion_result = find_by_emotion("ACHIEVEMENT", memory_file)
    assert emotion_result == [competition_memory]

    # 用户经历场景查询，验证大小写不影响结果
    scene_result = find_by_scene("LATE_NIGHT", memory_file)
    assert scene_result == [walk_memory]

    # 用户原始 text 关键词查询，验证大小写不影响结果
    text_result = search_by_text("competition", memory_file)
    assert text_result == [competition_memory]

    # 查询不到内容时应返回空列表
    assert find_by_emotion("sadness", memory_file) == []
    assert find_by_scene("rainy_day", memory_file) == []
    assert search_by_text("旅行", memory_file) == []

    # 使用统一格式输出查询到的历史记忆
    print("Emotion Result:")
    print(format_record(emotion_result[0].model_dump(mode="json")))

    print("\nScene Result:")
    print(format_record(scene_result[0].model_dump(mode="json")))

    print("\nText Result:")
    print(format_record(text_result[0].model_dump(mode="json")))

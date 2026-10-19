"""
测试 MusicMemory 语义检索功能。

需要本地 Ollama 已启动，
并且已经安装 bge-m3:latest 模型。
测试使用临时 memories.json，不会写入真实记忆文件。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory import MusicMemory, save_memory, semantic_search
from test.output_format import format_record


def create_memory(
    text: str,
    primary_emotion: str,
    scene: str,
) -> MusicMemory:
    """创建语义检索测试使用的 MusicMemory。"""
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


achievement_memory = create_memory(
    "比赛终于结束了，虽然很累，但我觉得之前的努力都很值得。",
    "achievement",
    "competition_finished",
)

calm_memory = create_memory(
    "晚上一个人在操场散步，心情很平静。",
    "calm",
    "late_night",
)

food_memory = create_memory(
    "今天晚上和朋友一起吃火锅，聊得很开心。",
    "joy",
    "dinner",
)

query = "忙了很久的一件事终于有了结果，虽然疲惫但很有成就感。"


# 临时目录会在测试结束后自动删除
with TemporaryDirectory() as temporary_directory:
    memory_file = Path(temporary_directory) / "database" / "local" / "memories.json"

    save_memory(achievement_memory, memory_file)
    save_memory(calm_memory, memory_file)
    save_memory(food_memory, memory_file)

    # 查询结果应按相似度从高到低排序，top_k=2 只返回前两条
    results = semantic_search(query, top_k=2, file_path=memory_file)
    assert len(results) == 2
    assert results[0].memory == achievement_memory
    assert results[0].similarity >= results[1].similarity

    # top_k 大于 Memory 数量时，应返回所有记录
    all_results = semantic_search(query, top_k=10, file_path=memory_file)
    assert len(all_results) == 3
    assert all_results[0].similarity >= all_results[1].similarity
    assert all_results[1].similarity >= all_results[2].similarity

    # 空 Memory 时应返回空列表
    empty_memory_file = Path(temporary_directory) / "empty" / "memories.json"
    assert semantic_search(query, file_path=empty_memory_file) == []

    # 空 query 和非法 top_k 都应被拒绝
    invalid_inputs = [
        ("", 3),
        ("   ", 3),
        (query, 0),
        (query, -1),
    ]

    for invalid_query, invalid_top_k in invalid_inputs:
        try:
            semantic_search(
                invalid_query,
                top_k=invalid_top_k,
                file_path=memory_file,
            )
            raise AssertionError("非法语义检索输入应该被拒绝。")
        except ValueError:
            pass

    # 使用统一格式输出相似度和对应的历史记忆
    display_results = [
        {
            "similarity": result.similarity,
            "memory": result.memory.model_dump(mode="json"),
        }
        for result in results
    ]

    print("Semantic Search Result:")
    for index, result in enumerate(display_results, start=1):
        print(f"\nTop {index}:")
        print(format_record(result))

"""
测试 MusicMemory 本地 JSON 存储

不调用 LLM，
不写入真实 memories.json，
只测试保存与读取流程。
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory import MusicMemory, load_memories, save_memory
from test.output_format import format_record


# 构造一条固定的测试记忆
memory = MusicMemory(
    text="今天终于完成比赛了，虽然很累，但是感觉很值得。",
    emotion={
        "primary_emotion": "achievement",
        "secondary_emotions": ["fatigue"],
        "scene": "completed_competition",
    },
    blueprint=MusicBlueprint(
        primary_emotion="achievement",
        secondary_emotions=["fatigue"],
        energy=0.8,
        valence=0.8,
        tempo=108,
        key="C Major",
        instruments=["piano", "guitar", "strings"],
        texture="warm",
        scene="celebration",
        progression="calm_to_rising",
    ),
)


# 临时目录会在测试结束后自动删除
with TemporaryDirectory() as temporary_directory:
    memory_file = Path(temporary_directory) / "database" / "local" / "memories.json"

    # 从不存在的文件读取，应得到空列表
    assert load_memories(memory_file) == []

    # 保存后应自动创建目录和 JSON 文件
    save_memory(memory, memory_file)
    assert memory_file.exists()

    # 重新读取，模拟程序重新启动后的恢复过程
    loaded_memories = load_memories(memory_file)
    assert len(loaded_memories) == 1

    loaded_memory = loaded_memories[0]
    assert loaded_memory.id == memory.id
    assert loaded_memory.text == memory.text
    assert loaded_memory.emotion == memory.emotion
    assert loaded_memory.blueprint == memory.blueprint
    assert loaded_memory.created_at == memory.created_at

    # 同一个记忆不能重复保存
    try:
        save_memory(memory, memory_file)
    except ValueError:
        pass
    else:
        raise AssertionError("重复 id 的记忆没有被拦截")

    # 损坏 JSON 文件时，读取必须明确报错
    memory_file.write_text("{损坏的 JSON", encoding="utf-8")

    try:
        load_memories(memory_file)
    except ValueError:
        pass
    else:
        raise AssertionError("损坏 JSON 文件没有被拦截")

    # JSON 格式正确但记录无效时，也必须明确报错
    memory_file.write_text('[{"text": "缺少其他字段"}]', encoding="utf-8")

    try:
        load_memories(memory_file)
    except ValueError:
        pass
    else:
        raise AssertionError("无效记忆数据没有被拦截")

    # 输出保存后读取回来的完整记忆
    print("Loaded Memory:")
    print(format_record(loaded_memory.model_dump(mode="json")))

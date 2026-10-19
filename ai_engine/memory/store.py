"""
用户音乐记忆本地存储模块

负责：
MusicMemory
    ↓
memories.json
    ↓
程序重新启动后恢复 MusicMemory
"""

import json
from pathlib import Path

from pydantic import ValidationError

from .schema import MusicMemory


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 默认本地记忆文件位置
MEMORY_FILE = PROJECT_ROOT / "database" / "local" / "memories.json"


def load_memories(file_path: Path | None = None) -> list[MusicMemory]:
    """
    从本地 JSON 文件读取所有音乐记忆。

    文件不存在时，说明还没有保存过记忆，返回空列表。
    """
    # 测试时可以传入临时文件，正常使用时保存到默认路径
    memory_file = file_path or MEMORY_FILE

    if not memory_file.exists():
        return []

    try:
        with memory_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"记忆文件 JSON 格式错误：{memory_file}") from error

    if not isinstance(data, list):
        raise ValueError("记忆文件最外层必须是 JSON 列表")

    try:
        return [MusicMemory.model_validate(memory_data) for memory_data in data]
    except ValidationError as error:
        raise ValueError("记忆文件中存在无效数据") from error


def save_memory(memory: MusicMemory, file_path: Path | None = None) -> None:
    """
    保存一条新的音乐记忆。

    file_path 仅用于测试时指定临时文件；正常使用时保存到 memories.json。
    """
    memory_file = file_path or MEMORY_FILE

    # 先读取已有记忆，保证不会覆盖旧数据
    memories = load_memories(memory_file)

    # 同一个 id 只能保存一次
    if any(saved_memory.id == memory.id for saved_memory in memories):
        raise ValueError(f"记忆已存在，不能重复保存：{memory.id}")

    memories.append(memory)

    # 第一次保存时自动创建目录
    memory_file.parent.mkdir(parents=True, exist_ok=True)

    data = [saved_memory.model_dump(mode="json") for saved_memory in memories]

    with memory_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

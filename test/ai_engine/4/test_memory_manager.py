"""
测试用户音乐记忆提交服务。

使用临时 memories.json 验证实际保存，
不写入项目真实的 database/local/memories.json。
"""

from datetime import timedelta
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import UUID

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.memory import commit_memory, load_memories, save_memory
from test.output_format import format_record


text = "今天终于完成比赛了，虽然很累，但是感觉很值得。"
emotion = {
    "primary_emotion": "achievement",
    "secondary_emotions": ["fatigue"],
    "scene": "completed_competition",
}
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


# 临时目录会在测试结束后自动删除
with TemporaryDirectory() as temporary_directory:
    memory_file = Path(temporary_directory) / "database" / "local" / "memories.json"

    # 测试时仍使用真实 save_memory()，但改写到临时文件
    def save_to_temporary_file(memory):
        save_memory(memory, memory_file)

    with patch(
        "ai_engine.memory.manager.save_memory",
        side_effect=save_to_temporary_file,
    ) as mock_save_memory:
        memory = commit_memory(text, emotion, blueprint)

    # 正常提交应调用保存，并生成完整的 MusicMemory
    mock_save_memory.assert_called_once_with(memory)
    assert isinstance(memory.id, UUID)
    assert memory.created_at.utcoffset() == timedelta(hours=8)
    assert memory.text == text
    assert memory.emotion.primary_emotion == "achievement"
    assert memory.blueprint == blueprint

    # 临时文件中的数据应能被完整恢复
    loaded_memories = load_memories(memory_file)
    assert loaded_memories == [memory]

    # 无效输入必须在写入前被 Pydantic 拒绝
    invalid_cases = [
        ("   ", emotion, blueprint),
        (
            text,
            {
                "primary_emotion": "achievement",
                "secondary_emotions": ["fatigue"],
            },
            blueprint,
        ),
        (
            text,
            emotion,
            {
                **blueprint.model_dump(),
                "energy": 1.2,
            },
        ),
    ]

    for invalid_text, invalid_emotion, invalid_blueprint in invalid_cases:
        with patch("ai_engine.memory.manager.save_memory") as mock_save_memory:
            try:
                commit_memory(
                    invalid_text,
                    invalid_emotion,
                    invalid_blueprint,
                )
                raise AssertionError("无效输入应该被拒绝。")
            except ValidationError:
                mock_save_memory.assert_not_called()

    # 保存失败时，异常必须直接暴露给调用方
    with patch(
        "ai_engine.memory.manager.save_memory",
        side_effect=OSError("临时文件无法写入"),
    ):
        try:
            commit_memory(text, emotion, blueprint)
            raise AssertionError("保存失败应该暴露异常。")
        except OSError:
            pass

    print("Committed Memory:")
    print(format_record(memory.model_dump(mode="json")))

"""Step 13.4：AudioArtifact 元数据契约测试，不写入真实 WAV 文件。"""

import json
from datetime import timedelta
from pathlib import Path
import sys
from uuid import UUID, uuid4

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.memory.schema import BEIJING_TIMEZONE
from music_engine import AudioArtifact, MusicGenerationSpec


draft_id = uuid4()
revision_id = uuid4()
spec = MusicGenerationSpec(
    caption="Warm instrumental music with piano and strings.",
    duration_seconds=20,
    bpm=92,
    key="C Major",
    instrumental=True,
    seed=20261006,
)
artifact = AudioArtifact(
    draft_id=draft_id,
    revision_id=revision_id,
    generation_spec=spec,
    provider_task_id="ace-task-001",
    content_type="audio/wav",
    file_path="database/local/audio/ace-task-001.wav",
)

# 正常创建、自动 ID/北京时间、Draft/Revision 关联与默认 Provider。
assert isinstance(artifact.id, UUID)
assert artifact.draft_id == draft_id
assert artifact.revision_id == revision_id
assert artifact.provider == "ace_step"
assert artifact.created_at.tzinfo == BEIJING_TIMEZONE
assert artifact.created_at.utcoffset() == timedelta(hours=8)

# 完整保存实际生成输入，且保存的是独立快照。
assert artifact.generation_spec == spec
assert artifact.generation_spec is not spec
assert json.loads(artifact.model_dump_json())["generation_spec"] == {
    "caption": "Warm instrumental music with piano and strings.",
    "duration_seconds": 20,
    "bpm": 92,
    "key": "C Major",
    "instrumental": True,
    "seed": 20261006,
}
spec.caption = "A later external change must not alter the artifact."
assert artifact.generation_spec.caption == "Warm instrumental music with piano and strings."

# 元数据不能携带二进制音频；文件只由将来的 file_path 指向。
assert "audio_bytes" not in AudioArtifact.model_fields
assert "audio_bytes" not in artifact.model_dump()

# 必填定位字段与 UUID 均由 Pydantic 校验。
for field_name in ("provider_task_id", "content_type", "file_path"):
    try:
        AudioArtifact(
            draft_id=draft_id,
            revision_id=revision_id,
            generation_spec=spec,
            **{field_name: "   "},
        )
        raise AssertionError(f"{field_name} 空白时应该被拒绝")
    except ValidationError:
        pass

try:
    AudioArtifact(
        draft_id="not-a-uuid",
        revision_id=revision_id,
        generation_spec=spec,
        provider_task_id="ace-task-001",
        content_type="audio/wav",
        file_path="database/local/audio/example.wav",
    )
    raise AssertionError("无效 UUID 应该被拒绝")
except ValidationError:
    pass

try:
    AudioArtifact(
        draft_id=draft_id,
        revision_id=revision_id,
        generation_spec={"caption": "", "bpm": 92, "key": "C Major"},
        provider_task_id="ace-task-001",
        content_type="audio/wav",
        file_path="database/local/audio/example.wav",
    )
    raise AssertionError("无效 MusicGenerationSpec 应该被拒绝")
except ValidationError:
    pass

print("AudioArtifact Schema: all checks passed.")

"""Music Companion POC 结果的轻量持久化，不改动正式音频资产。"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from music_companion.schema import MusicInterpretationResult


class MusicCompanionResultStore:
    """按 AudioArtifact ID 缓存已完成的解读，避免重复加载模型。"""

    def __init__(self, data_root: Path | str) -> None:
        self.path = Path(data_root) / "music_companion_interpretations.json"

    def get(self, audio_artifact_id: UUID | str) -> MusicInterpretationResult | None:
        payload = self._read()
        item = payload.get(str(audio_artifact_id))
        return MusicInterpretationResult.model_validate(item) if item else None

    def save(self, result: MusicInterpretationResult) -> None:
        payload = self._read()
        payload[str(result.audio_artifact_id)] = result.model_dump(mode="json")
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _read(self) -> dict[str, object]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Music Companion 解读缓存无法读取") from error
        if not isinstance(payload, dict):
            raise ValueError("Music Companion 解读缓存格式无效")
        return payload

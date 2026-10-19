"""手动验证 MuseGarden AceStepClient；不写入任何正式音频目录。"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_engine import MusicGenerationSpec
from music_engine.providers import AceStepClient


def main() -> None:
    spec = MusicGenerationSpec(
        caption=(
            "Warm instrumental music with piano and strings. "
            "A satisfying and positive emotional atmosphere. Moderate energy. "
            "Begin calmly and gradually become brighter and more uplifting."
        ),
        duration_seconds=20,
        bpm=92,
        key="C Major",
        instrumental=True,
        seed=20261005,
    )
    result = AceStepClient().generate_audio(spec)
    print(f"task_id: {result.task_id}")
    print(f"content_type: {result.content_type}")
    print(f"audio_bytes: {len(result.audio_bytes)}")


if __name__ == "__main__":
    main()

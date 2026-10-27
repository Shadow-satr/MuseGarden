"""启动本地 Garden/创作 API，并首次创建稳定预览数据。"""

import os
import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.api import run_server
from backend.app.services import build_preview_service
from application import CreationService
from flower_engine import Garden
from music_engine import AudioStore, MusicGenerationService
from music_engine.providers import AceStepClient
from scripts.export_garden_preview_spec import build_preview_domain


DATA_ROOT = Path(os.environ.get("MUSEGARDEN_DATA_ROOT", PROJECT_ROOT / "database" / "preview"))


def test_flower_size_roll() -> Callable[[], float] | None:
    """返回仅供隔离验收环境使用的确定性大小随机源。

    正式启动不设置该环境变量，CreationService 仍使用默认的 random.random。测试运行可用
    例如 ``0.9,0.1`` 的序列分别强制一次 small、一次 large，而不向 HTTP 接口暴露参数。
    """
    raw = os.environ.get("MUSEGARDEN_TEST_FLOWER_SIZE_ROLLS")
    if not raw:
        return None
    rolls = tuple(float(value.strip()) for value in raw.split(","))
    if not rolls or any(not 0 <= value <= 1 for value in rolls):
        raise ValueError("MUSEGARDEN_TEST_FLOWER_SIZE_ROLLS 必须是 0 到 1 之间的逗号分隔数值")
    index = 0

    def next_roll() -> float:
        nonlocal index
        result = rolls[min(index, len(rolls) - 1)]
        index += 1
        return result

    return next_roll


def seed_preview_service():
    service = build_preview_service(DATA_ROOT)
    garden, artifacts, plantings = build_preview_domain()
    if os.environ.get("MUSEGARDEN_TEST_TERRAIN_GARDEN") == "1":
        # Step 14.1 uses an empty current-size garden. This is test-only bootstrap data;
        # normal preview startup continues to preserve its existing persisted garden.
        garden = Garden(id=garden.id, name=garden.name, width=91, height=68)
        artifacts = ()
        plantings = ()
    if service.garden_store.get_garden(garden.id) is None:
        service.garden_store.save_garden(garden)
        for artifact in artifacts:
            service.flower_store.save(artifact)
        for planting in plantings:
            service.garden_store.save_planting(planting)
    return service, garden.id


def main() -> None:
    service, garden_id = seed_preview_service()
    audio_store = AudioStore(DATA_ROOT)
    music_service = MusicGenerationService(AceStepClient(), audio_store)
    roll = test_flower_size_roll()
    creation_service = (
        CreationService(data_root=DATA_ROOT, music_service=music_service, flower_size_roll=roll)
        if roll is not None
        else CreationService(data_root=DATA_ROOT, music_service=music_service)
    )
    port = int(os.environ.get("MUSEGARDEN_API_PORT", "8000"))
    run_server(service, garden_id, port=port, creation_service=creation_service)


if __name__ == "__main__":
    main()

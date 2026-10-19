"""启动本地 Garden/创作 API，并首次创建稳定预览数据。"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.api import run_server
from backend.app.services import build_preview_service
from application import CreationService
from music_engine import AudioStore, MusicGenerationService
from music_engine.providers import AceStepClient
from scripts.export_garden_preview_spec import build_preview_domain


DATA_ROOT = PROJECT_ROOT / "database" / "preview"


def seed_preview_service():
    service = build_preview_service(DATA_ROOT)
    garden, artifacts, plantings = build_preview_domain()
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
    creation_service = CreationService(
        data_root=DATA_ROOT,
        music_service=MusicGenerationService(AceStepClient(), audio_store),
    )
    run_server(service, garden_id, creation_service=creation_service)


if __name__ == "__main__":
    main()

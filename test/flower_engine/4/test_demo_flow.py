"""Step 12：AI → Music → Flower → Garden 的应用层闭环。"""

from pathlib import Path

import pytest

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import CreationDraft
from ai_engine.memory.schema import EmotionSnapshot
from ai_engine.memory.store import load_memories
from application import CreationService
from backend.app.api.garden_preview import _json_safe_payload
from flower_engine import GardenService
from music_engine import AceStepGenerationResult, AudioStore, MusicGenerationService
from scripts import run_garden_preview_api as preview_api


def make_blueprint() -> MusicBlueprint:
    return MusicBlueprint(
        primary_emotion="满足感",
        secondary_emotions=["喜悦"],
        energy=0.7,
        valence=0.8,
        tempo=108,
        key="C Major",
        instruments=["piano"],
        texture="温暖",
        scene="比赛结束之后",
        progression="calm_to_rising",
    )


class FakeMusicClient:
    def __init__(self) -> None:
        self.specs = []

    def generate_audio(self, spec):
        self.specs.append(spec)
        return AceStepGenerationResult(
            task_id=f"fake-{len(self.specs)}",
            audio_bytes=f"RIFF-test-v{len(self.specs)}".encode(),
            content_type="audio/wav",
        )


def make_service(
    tmp_path: Path,
    *,
    garden_size: tuple[int, int] = (4, 4),
    flower_size_roll=lambda: 0.9,
):
    client = FakeMusicClient()
    seen_texts = []

    def ai_pipeline(text: str) -> CreationDraft:
        seen_texts.append(text)
        return CreationDraft(
            text=text,
            emotion=EmotionSnapshot(
                primary_emotion="满足感",
                secondary_emotions=["喜悦"],
                scene="比赛结束之后",
            ),
            blueprint=make_blueprint(),
        )

    def editor(text, current, instruction):
        assert instruction == "更温暖一点"
        assert text == "比赛结束后终于松了一口气"
        return current.model_copy(update={"texture": "soft", "tempo": 92})

    audio_store = AudioStore(tmp_path)
    service = CreationService(
        data_root=tmp_path,
        music_service=MusicGenerationService(client, audio_store),
        blueprint_pipeline=ai_pipeline,
        blueprint_editor=editor,
        flower_size_roll=flower_size_roll,
    )
    garden = GardenService(service.garden_store, service.flower_store).create_garden(
        "测试花园", *garden_size
    )
    return service, garden, client, seen_texts


def test_create_memory_persists_all_four_engine_outputs(tmp_path: Path) -> None:
    service, garden, client, seen_texts = make_service(tmp_path)

    result = service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))

    assert seen_texts == ["比赛结束后终于松了一口气"]
    assert client.specs[0].bpm == result["blueprint"]["tempo"]
    assert result["flower"]["species"] == result["flower"]["render_spec"]["species"]
    assert result["music"]["version"] == 1
    assert service.audio_store.load_audio(result["music"]["artifact_id"]) == b"RIFF-test-v1"
    assert len(load_memories(tmp_path / "memories.json")) == 1
    assert len(service.final_store.list_all()) == 1
    assert len(service.flower_store.list_all()) == 1
    assert len(service.garden_store.list_plantings(garden.id)) == 1
    assert service.list_creations(garden.id) == [result]


@pytest.mark.parametrize(
    ("roll", "expected_size", "expected_tiles"),
    [(0.0, "large", 9), (0.9, "small", 1)],
)
def test_terrain_garden_persists_injected_flower_size_once(
    tmp_path: Path,
    roll: float,
    expected_size: str,
    expected_tiles: int,
) -> None:
    service, garden, _, _ = make_service(
        tmp_path,
        garden_size=(91, 68),
        flower_size_roll=lambda: roll,
    )
    created = service.create_memory("比赛结束后终于松了一口气", garden.id, (22, 18))
    planting = service.garden_store.list_plantings(garden.id)[0]
    assert created["flower"]["size"] == expected_size
    assert created["planting"]["flower_size"] == expected_size
    assert planting.flower_size == expected_size
    assert len(planting.occupied_tiles) == expected_tiles
    assert service.list_creations(garden.id)[0]["planting"]["occupied_tiles"] == [
        list(tile) for tile in planting.occupied_tiles
    ]


def test_music_regeneration_keeps_flower_and_planting_unchanged(tmp_path: Path) -> None:
    service, garden, client, _ = make_service(tmp_path)
    original = service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))
    flower_before = service.flower_store.get(original["flower"]["artifact_id"]).model_dump(mode="json")
    planting_before = [item.model_dump(mode="json") for item in service.garden_store.list_plantings(garden.id)]

    updated = service.regenerate_music(original["creation_id"], "更温暖一点")

    assert updated["music"]["version"] == 2
    assert updated["music"]["artifact_id"] != original["music"]["artifact_id"]
    assert client.specs[-1].bpm == 92
    assert updated["blueprint"]["tempo"] == 92
    assert updated["blueprint"]["texture"] == "soft"
    assert updated["text"] == original["text"]
    assert updated["latest_music_version"] == 2
    assert [item["version"] for item in updated["music_versions"]] == [1, 2]
    assert len({item["version_id"] for item in updated["music_versions"]}) == 2
    assert updated["music_versions"][1]["modification_text"] == "更温暖一点"
    assert service.audio_store.load_audio(original["music"]["artifact_id"]) == b"RIFF-test-v1"
    assert service.audio_store.load_audio(updated["music"]["artifact_id"]) == b"RIFF-test-v2"
    assert updated["flower"] == original["flower"]
    assert updated["planting"] == original["planting"]
    assert service.flower_store.get(original["flower"]["artifact_id"]).model_dump(mode="json") == flower_before
    assert [item.model_dump(mode="json") for item in service.garden_store.list_plantings(garden.id)] == planting_before
    assert len(service.flower_store.list_all()) == 1


def test_selecting_history_persists_without_changing_memory_or_flower(tmp_path: Path) -> None:
    service, garden, _, _ = make_service(tmp_path)
    original = service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))
    revised = service.regenerate_music(original["creation_id"], "更温暖一点")

    selected = service.select_music_version(
        original["creation_id"], original["music"]["artifact_id"]
    )

    assert selected["music"]["version"] == 1
    assert selected["music"]["artifact_id"] == original["music"]["artifact_id"]
    assert selected["latest_music_version"] == 2
    assert selected["text"] == original["text"]
    assert selected["flower"] == original["flower"]
    assert selected["planting"] == original["planting"]
    assert [item["audio_artifact_id"] for item in selected["music_versions"]] == [
        original["music"]["artifact_id"], revised["music"]["artifact_id"],
    ]
    assert service.list_creations(garden.id)[0]["music"]["version"] == 1


def test_renaming_music_version_persists_without_changing_audio_or_flower(tmp_path: Path) -> None:
    service, garden, _, _ = make_service(tmp_path)
    original = service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))
    legacy_record = service.records.get(original["creation_id"])
    assert legacy_record is not None
    service.records.replace(legacy_record.model_copy(update={"music_versions": ()}))

    renamed = service.rename_music_version(
        original["creation_id"], original["music"]["artifact_id"], "晨光版"
    )

    assert renamed["music_versions"][0]["display_name"] == "晨光版"
    assert renamed["music"]["artifact_id"] == original["music"]["artifact_id"]
    assert renamed["flower"] == original["flower"]


def test_failed_revision_keeps_current_and_history_unchanged(tmp_path: Path) -> None:
    service, garden, client, _ = make_service(tmp_path)
    original = service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))

    def fail(_):
        raise RuntimeError("音乐服务不可用")

    client.generate_audio = fail
    with pytest.raises(RuntimeError, match="音乐服务不可用"):
        service.regenerate_music(original["creation_id"], "更温暖一点")

    retained = service.list_creations(garden.id)[0]
    assert retained["music"]["artifact_id"] == original["music"]["artifact_id"]
    assert retained["latest_music_version"] == 1
    assert len(retained["music_versions"]) == 1


def test_invalid_or_occupied_position_stops_before_ai_and_music(tmp_path: Path) -> None:
    service, garden, client, seen_texts = make_service(tmp_path)
    with pytest.raises(ValueError, match="0 到 3"):
        service.create_memory("测试", garden.id, (4, 1))
    service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))
    with pytest.raises(ValueError, match="已经有花"):
        service.create_memory("另一次回忆", garden.id, (2, 1))
    assert len(seen_texts) == 1
    assert len(client.specs) == 1


def test_failed_music_generation_does_not_plant_or_save_flower(tmp_path: Path) -> None:
    service, garden, client, _ = make_service(tmp_path)

    def fail(_):
        raise RuntimeError("音乐服务不可用")

    client.generate_audio = fail
    with pytest.raises(RuntimeError, match="音乐服务不可用"):
        service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))
    assert service.flower_store.list_all() == []
    assert service.garden_store.list_plantings(garden.id) == []
    assert service.records.list_all() == []


def test_application_layer_is_only_cross_engine_import_site() -> None:
    root = Path(__file__).resolve().parents[3]
    music_source = (root / "music_engine" / "service.py").read_text(encoding="utf-8")
    flower_source = (root / "flower_engine" / "binding.py").read_text(encoding="utf-8")
    assert "flower_engine" not in music_source
    assert "AudioArtifact" not in flower_source


def test_http_payload_preserves_63_bit_variation_seed() -> None:
    original = {"garden": {"flowers": [{"render_spec": {"variation_seed": 603703287136832921}}]}}
    converted = _json_safe_payload(original)
    assert converted == {"garden": {"flowers": [{"render_spec": {"variation_seed": "603703287136832921"}}]}}
    assert original["garden"]["flowers"][0]["render_spec"]["variation_seed"] == 603703287136832921


def test_dig_up_removes_flower_but_keeps_memory_and_audio(tmp_path: Path) -> None:
    service, garden, _, _ = make_service(tmp_path)
    created = service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))
    flower_id = created["flower"]["artifact_id"]
    planting_id = created["planting"]["record_id"]
    audio_id = created["music"]["artifact_id"]

    service.dig_up_flower(garden.id, planting_id)

    assert service.garden_store.list_plantings(garden.id) == []
    assert service.flower_store.get(flower_id) is None
    assert len(load_memories(tmp_path / "memories.json")) == 1
    assert len(service.final_store.list_all()) == 1
    assert service.audio_store.load_audio(audio_id) == b"RIFF-test-v1"
    retained = service.list_creations(garden.id)[0]
    assert retained["flower"] is None
    assert retained["planting"] is None
    assert retained["music"]["artifact_id"] == audio_id
    with pytest.raises(ValueError, match="此花不在指定花园中"):
        service.dig_up_flower(garden.id, planting_id)


def test_dig_up_keeps_shared_artifact_until_last_planting(tmp_path: Path) -> None:
    service, garden, _, _ = make_service(tmp_path)
    created = service.create_memory("比赛结束后终于松了一口气", garden.id, (2, 1))
    flower_id = created["flower"]["artifact_id"]
    second = service.gardens.plant_flower(garden.id, flower_id, 1, 1)

    service.dig_up_flower(garden.id, created["planting"]["record_id"])
    assert service.flower_store.get(flower_id) is not None
    assert [item.id for item in service.garden_store.list_plantings(garden.id)] == [second.id]

    service.dig_up_flower(garden.id, second.id)
    assert service.flower_store.get(flower_id) is None


def test_preview_bootstrap_does_not_restore_dug_up_flower(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(preview_api, "DATA_ROOT", tmp_path)
    interaction, garden_id = preview_api.seed_preview_service()
    removed = interaction.garden_store.list_plantings(garden_id)[0]
    interaction.garden_service.dig_up_flower(garden_id, removed.id)

    restarted, _ = preview_api.seed_preview_service()
    assert removed.id not in {
        item.id for item in restarted.garden_store.list_plantings(garden_id)
    }
    assert restarted.flower_store.get(removed.flower_artifact_id) is None

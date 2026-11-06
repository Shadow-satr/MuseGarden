"""一次记忆创作与后续音乐版本修改的应用层编排。"""

import json
import random
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ai_engine.blueprint.editor import edit_blueprint
from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.creation.schema import BlueprintRevision, CreationDraft
from ai_engine.memory.schema import MusicMemory
from ai_engine.memory.store import save_memory
from ai_engine.pipeline import run_creation_pipeline
from application.garden_planting import plan_planting
from flower_engine import (
    FlowerArtifactStore,
    FlowerLifecycleService,
    GardenService,
    GardenStore,
)
from music_engine import AudioStore, FinalCreation, FinalCreationStore, MusicGenerationService, MusicVersionService


class DemoMusicVersion(BaseModel):
    revision_id: UUID
    audio_artifact_id: UUID
    version: int = Field(ge=1)
    modification_text: str | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=60)
    created_at: datetime


class DemoCreationRecord(BaseModel):
    """Demo 页面可恢复的当前音乐选择，花朵和位置只保存引用。"""

    creation_id: UUID
    text: str = Field(min_length=1)
    garden_id: UUID
    flower_artifact_id: UUID | None
    planting_record_id: UUID | None
    current_audio_artifact_id: UUID
    music_blueprint: MusicBlueprint
    music_revision: int = Field(ge=1)
    music_versions: tuple[DemoMusicVersion, ...] = ()
    blueprint_revisions: tuple[BlueprintRevision, ...] = ()

    @field_validator("music_blueprint")
    @classmethod
    def copy_music_blueprint(cls, value: MusicBlueprint) -> MusicBlueprint:
        return MusicBlueprint.model_validate(value.model_dump())


class DemoCreationStore:
    def __init__(self, data_root: Path) -> None:
        self.file_path = Path(data_root) / "demo_creations.json"

    def list_all(self) -> list[DemoCreationRecord]:
        if not self.file_path.exists():
            return []
        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Demo 创作记录必须是 JSON 列表")
        return [DemoCreationRecord.model_validate(item) for item in data]

    def get(self, creation_id: UUID | str) -> DemoCreationRecord | None:
        target = UUID(str(creation_id))
        return next((item for item in self.list_all() if item.creation_id == target), None)

    def save(self, record: DemoCreationRecord) -> None:
        records = self.list_all()
        if any(item.creation_id == record.creation_id for item in records):
            raise ValueError("Demo 创作记录已存在")
        self._write([*records, record])

    def replace(self, record: DemoCreationRecord) -> None:
        records = self.list_all()
        if not any(item.creation_id == record.creation_id for item in records):
            raise ValueError("Demo 创作记录不存在")
        self._write([
            record if item.creation_id == record.creation_id else item
            for item in records
        ])

    def _write(self, records: list[DemoCreationRecord]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.file_path.with_name(f"{self.file_path.name}.tmp")
        try:
            temporary.write_text(
                json.dumps([item.model_dump(mode="json") for item in records], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.file_path)
        finally:
            temporary.unlink(missing_ok=True)


class CreationService:
    """调用既有 Engine，保存创作并返回可供页面展示的关系。"""

    def __init__(
        self,
        *,
        data_root: Path,
        music_service: MusicGenerationService,
        blueprint_pipeline: Callable[[str], CreationDraft] | None = None,
        blueprint_editor: Callable[[str, MusicBlueprint, str], MusicBlueprint] = edit_blueprint,
        flower_size_roll: Callable[[], float] = random.random,
    ) -> None:
        self.data_root = Path(data_root)
        self.music_service = music_service
        self.blueprint_pipeline = blueprint_pipeline or (
            lambda text: run_creation_pipeline(text, use_memory=False)
        )
        self.blueprint_editor = blueprint_editor
        self.flower_size_roll = flower_size_roll
        self.audio_store = music_service.audio_store
        self.music_version_service = MusicVersionService(self.audio_store)
        self.garden_store = GardenStore(data_root)
        self.flower_store = FlowerArtifactStore(data_root)
        self.final_store = FinalCreationStore(data_root)
        self.records = DemoCreationStore(data_root)
        self.gardens = GardenService(self.garden_store, self.flower_store)
        self.flowers = FlowerLifecycleService(self.final_store, self.flower_store)

    def create_memory(
        self,
        text: str,
        garden_id: UUID | str,
        position: tuple[int, int],
    ) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("记忆文字不能为空")
        if not isinstance(position, tuple) or len(position) != 2:
            raise ValueError("position 必须为 (x, y)")
        x, y = position
        garden = self.garden_store.get_garden(garden_id)
        if garden is None:
            raise ValueError(f"Garden 不存在：{garden_id}")
        uses_terrain_map = garden.width >= 91 and garden.height >= 68
        plan = plan_planting(
            (x, y),
            self.garden_store.list_plantings(garden.id),
            prefer_large=self.flower_size_roll() < 0.5,
        ) if uses_terrain_map else None
        if plan is None:
            self.gardens.validate_planting_position(garden.id, x, y)

        draft = self.blueprint_pipeline(text.strip())
        revision = BlueprintRevision(
            draft_id=draft.id,
            version=1,
            blueprint=draft.blueprint,
        )
        audio = self.music_service.generate_for_revision(
            draft_id=draft.id,
            revision=revision,
        )
        memory = MusicMemory(
            id=draft.id,
            text=draft.text,
            emotion=draft.emotion,
            blueprint=draft.blueprint,
        )
        save_memory(memory, self.data_root / "memories.json")
        final = FinalCreation(
            draft_id=draft.id,
            revision_id=revision.id,
            memory_id=memory.id,
            audio_artifact_id=audio.id,
            blueprint=draft.blueprint,
            audio_artifact=audio,
        )
        self.final_store.save(final)
        seed = final.id.int & ((1 << 63) - 1)
        flower = self.flowers.create_for_creation(final.id, seed)
        planting = self.gardens.plant_flower(
            garden.id,
            flower.id,
            x,
            y,
            placement_schema_version="terrain-v1" if plan else "legacy",
            flower_size=plan.flower_size if plan else "small",
            occupied_tiles=plan.occupied_tiles if plan else (),
        )
        record = DemoCreationRecord(
            creation_id=final.id,
            text=draft.text,
            garden_id=garden.id,
            flower_artifact_id=flower.id,
            planting_record_id=planting.id,
            current_audio_artifact_id=audio.id,
            music_blueprint=final.blueprint,
            music_revision=1,
            music_versions=(DemoMusicVersion(
                revision_id=revision.id,
                audio_artifact_id=audio.id,
                version=1,
                display_name="初始版本",
                created_at=audio.created_at,
            ),),
            blueprint_revisions=(revision,),
        )
        self.records.save(record)
        return self.describe(record)

    def regenerate_music(self, creation_id: UUID | str, modification_text: str) -> dict:
        if not isinstance(modification_text, str) or not modification_text.strip():
            raise ValueError("音乐修改要求不能为空")
        record = self.records.get(creation_id)
        if record is None:
            raise ValueError("创作不存在")
        final = self.final_store.get(record.creation_id)
        if final is None:
            raise RuntimeError("创作缺少已归档的 Blueprint")
        record = self._with_version_history(record, final, persist=True)
        selected_version = next(
            version for version in record.music_versions
            if version.audio_artifact_id == record.current_audio_artifact_id
        )
        selected_revision = next(
            (revision for revision in record.blueprint_revisions
             if revision.id == selected_version.revision_id),
            None,
        )
        if selected_revision is not None:
            base_blueprint = selected_revision.blueprint
        elif selected_version.revision_id == final.revision_id:
            base_blueprint = final.blueprint
        else:
            raise ValueError("当前音乐版本没有保存 Blueprint，无法基于此版本修改")
        edited = self.blueprint_editor(
            record.text,
            base_blueprint.model_copy(deep=True),
            modification_text.strip(),
        )
        revision = BlueprintRevision(
            draft_id=final.draft_id,
            version=max(version.version for version in record.music_versions) + 1,
            edit_instruction=modification_text.strip(),
            blueprint=edited,
        )
        audio = self.music_service.generate_for_revision(
            draft_id=final.draft_id,
            revision=revision,
        )
        next_record = record.model_copy(update={
            "current_audio_artifact_id": audio.id,
            "music_blueprint": edited,
            "music_revision": revision.version,
            "music_versions": (*record.music_versions, DemoMusicVersion(
                revision_id=revision.id,
                audio_artifact_id=audio.id,
                version=revision.version,
                modification_text=modification_text.strip(),
                display_name=f"音乐版本 {revision.version}",
                created_at=audio.created_at,
            )),
            "blueprint_revisions": (*record.blueprint_revisions, revision),
        })
        self.records.replace(next_record)
        return self.describe(next_record)

    def select_music_version(
        self,
        creation_id: UUID | str,
        audio_artifact_id: UUID | str,
    ) -> dict:
        record = self.records.get(creation_id)
        if record is None:
            raise ValueError("创作不存在")
        final = self.final_store.get(record.creation_id)
        if final is None:
            raise RuntimeError("创作缺少已归档的 Blueprint")
        record = self._with_version_history(record, final, persist=True)
        target_audio_id = UUID(str(audio_artifact_id))
        if not any(version.audio_artifact_id == target_audio_id for version in record.music_versions):
            raise ValueError("音乐版本不属于这段记忆")
        audio = self.audio_store.get(target_audio_id)
        if audio is None or audio.draft_id != final.draft_id:
            raise ValueError("音乐版本不存在或归属错误")
        selected = record.model_copy(update={"current_audio_artifact_id": target_audio_id})
        self.records.replace(selected)
        return self.describe(selected)

    def rename_music_version(
        self,
        creation_id: UUID | str,
        audio_artifact_id: UUID | str,
        display_name: str,
    ) -> dict:
        name = display_name.strip()
        if not name:
            raise ValueError("版本名称不能为空")
        record = self.records.get(creation_id)
        if record is None:
            raise ValueError("创作不存在")
        final = self.final_store.get(record.creation_id)
        if final is None:
            raise RuntimeError("创作缺少已归档的 Blueprint")
        record = self._with_version_history(record, final, persist=True)
        target_audio_id = UUID(str(audio_artifact_id))
        target = next((item for item in record.music_versions if item.audio_artifact_id == target_audio_id), None)
        if target is None:
            raise ValueError("音乐版本不属于这段记忆")
        renamed = record.model_copy(update={
            "music_versions": tuple(
                item.model_copy(update={"display_name": name}) if item.audio_artifact_id == target_audio_id else item
                for item in record.music_versions
            ),
        })
        self.records.replace(renamed)
        return self.describe(renamed)

    def list_creations(self, garden_id: UUID | str) -> list[dict]:
        target = UUID(str(garden_id))
        return [
            self.describe(record)
            for record in self.records.list_all()
            if record.garden_id == target
        ]

    def dig_up_flower(self, garden_id: UUID | str, planting_record_id: UUID | str) -> None:
        target_garden = UUID(str(garden_id))
        target_planting = UUID(str(planting_record_id))
        record = next(
            (item for item in self.records.list_all()
             if item.garden_id == target_garden and item.planting_record_id == target_planting),
            None,
        )
        self.gardens.dig_up_flower(target_garden, target_planting)
        if record is not None:
            self.records.replace(record.model_copy(update={
                "flower_artifact_id": None,
                "planting_record_id": None,
            }))

    def describe(self, record: DemoCreationRecord) -> dict:
        final = self.final_store.get(record.creation_id)
        flower = self.flower_store.get(record.flower_artifact_id) if record.flower_artifact_id else None
        if final is None:
            raise RuntimeError("创作引用的资产不存在")
        record = self._with_version_history(record, final, persist=False)
        audio = self.audio_store.get(record.current_audio_artifact_id)
        if audio is None:
            raise RuntimeError("创作引用的资产不存在")
        selected_version = next(
            (item for item in record.music_versions if item.audio_artifact_id == audio.id),
            None,
        )
        if selected_version is None:
            raise RuntimeError("当前音乐不属于创作的版本历史")
        selected_revision = next(
            (revision for revision in record.blueprint_revisions
             if revision.id == selected_version.revision_id),
            None,
        )
        selected_blueprint = (
            selected_revision.blueprint
            if selected_revision is not None
            else final.blueprint if selected_version.revision_id == final.revision_id
            else None
        )
        planting = next(
            (
                item for item in self.garden_store.list_plantings(record.garden_id)
                if item.id == record.planting_record_id
            ),
            None,
        ) if record.planting_record_id else None
        return {
            "creation_id": str(record.creation_id),
            "text": record.text,
            "blueprint": record.music_blueprint.model_dump(mode="json"),
            "selected_blueprint": selected_blueprint.model_dump(mode="json") if selected_blueprint else None,
            "flower": {
                "artifact_id": str(flower.id),
                "species": flower.species,
                "render_spec": flower.render_spec.model_dump(mode="json"),
                "size": planting.flower_size,
                "occupied_tiles": [list(tile) for tile in planting.occupied_tiles],
            } if flower is not None and planting is not None else None,
            "music": {
                "artifact_id": str(audio.id),
                "version": selected_version.version,
                "url": f"/api/audio/{audio.id}",
            },
            "latest_music_version": record.music_revision,
            "music_versions": [
                {
                    "version_id": str(version.revision_id),
                    "audio_artifact_id": str(version.audio_artifact_id),
                    "version": version.version,
                    "modification_text": version.modification_text,
                    "display_name": version.display_name or ("初始版本" if version.version == 1 else f"音乐版本 {version.version}"),
                    "created_at": version.created_at.isoformat(),
                    "url": f"/api/audio/{version.audio_artifact_id}",
                    "is_latest": version.version == record.music_revision,
                    "is_selected": version.audio_artifact_id == record.current_audio_artifact_id,
                }
                for version in record.music_versions
            ],
            "planting": {
                "record_id": str(record.planting_record_id),
                "x": planting.x,
                "y": planting.y,
                "placement_schema_version": planting.placement_schema_version,
                "flower_size": planting.flower_size,
                "occupied_tiles": [list(tile) for tile in planting.occupied_tiles],
            } if planting is not None and flower is not None else None,
        }

    def _with_version_history(
        self,
        record: DemoCreationRecord,
        final: FinalCreation,
        *,
        persist: bool,
    ) -> DemoCreationRecord:
        if record.music_versions:
            return record
        artifacts = self.music_version_service.list_for_draft(final.draft_id)
        if not artifacts:
            raise RuntimeError("创作没有可用的音乐版本")
        versions = tuple(
            DemoMusicVersion(
                revision_id=artifact.revision_id,
                audio_artifact_id=artifact.id,
                version=index,
                created_at=artifact.created_at,
            )
            for index, artifact in enumerate(artifacts, start=1)
        )
        initial_revision = BlueprintRevision(
            id=final.revision_id,
            draft_id=final.draft_id,
            version=1,
            blueprint=final.blueprint,
            created_at=final.confirmed_at,
        )
        migrated = record.model_copy(update={
            "music_versions": versions,
            "blueprint_revisions": record.blueprint_revisions or (initial_revision,),
            "music_revision": max(record.music_revision, len(versions)),
        })
        if persist:
            self.records.replace(migrated)
        return migrated

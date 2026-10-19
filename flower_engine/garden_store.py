"""Garden 与 PlantingRecord 的最小本地 JSON 持久化。"""

import json
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from flower_engine.schema import Garden, PlantingRecord


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA_ROOT = PROJECT_ROOT / "database" / "local"


class GardenStore:
    """分别保存空间容器和种植记录，不承担种植业务规则。"""

    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = Path(data_root) if data_root else LOCAL_DATA_ROOT
        self.gardens_file = self.data_root / "gardens.json"
        self.plantings_file = self.data_root / "planting_records.json"

    def save_garden(self, garden: Garden) -> None:
        if not isinstance(garden, Garden):
            raise TypeError("garden 必须是 Garden 实例")
        gardens = self.list_gardens()
        if any(item.id == garden.id for item in gardens):
            raise ValueError(f"Garden 已存在：{garden.id}")
        self._write_gardens([*gardens, garden])

    def get_garden(self, garden_id: UUID | str) -> Garden | None:
        target_id = _normalize_uuid(garden_id)
        return next(
            (garden for garden in self.list_gardens() if garden.id == target_id),
            None,
        )

    def list_gardens(self) -> list[Garden]:
        if not self.gardens_file.exists():
            return []
        data = _load_json_list(self.gardens_file, "花园")
        try:
            return [Garden.model_validate(item) for item in data]
        except ValidationError as error:
            raise ValueError("花园数据中存在无效记录") from error

    def save_planting(self, planting: PlantingRecord) -> None:
        if not isinstance(planting, PlantingRecord):
            raise TypeError("planting 必须是 PlantingRecord 实例")
        plantings = self.list_plantings()
        if any(item.id == planting.id for item in plantings):
            raise ValueError(f"PlantingRecord 已存在：{planting.id}")
        self._write_plantings([*plantings, planting])

    def delete_planting(self, planting_id: UUID | str) -> PlantingRecord:
        target_id = _normalize_uuid(planting_id)
        plantings = self.list_plantings()
        target = next((item for item in plantings if item.id == target_id), None)
        if target is None:
            raise ValueError(f"PlantingRecord 不存在：{target_id}")
        self._write_plantings([item for item in plantings if item.id != target_id])
        return target

    def list_plantings(
        self,
        garden_id: UUID | str | None = None,
    ) -> list[PlantingRecord]:
        if not self.plantings_file.exists():
            return []
        data = _load_json_list(self.plantings_file, "种植记录")
        try:
            plantings = [PlantingRecord.model_validate(item) for item in data]
        except ValidationError as error:
            raise ValueError("种植数据中存在无效记录") from error

        if garden_id is not None:
            target_id = _normalize_uuid(garden_id)
            plantings = [
                planting
                for planting in plantings
                if planting.garden_id == target_id
            ]
        return sorted(plantings, key=lambda planting: planting.planted_at)

    def _write_gardens(self, gardens: list[Garden]) -> None:
        _write_json_models(self.gardens_file, gardens)

    def _write_plantings(self, plantings: list[PlantingRecord]) -> None:
        _write_json_models(self.plantings_file, plantings)


def _load_json_list(file_path: Path, label: str) -> list[object]:
    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} JSON 格式错误：{file_path}") from error
    if not isinstance(data, list):
        raise ValueError(f"{label}最外层必须是 JSON 列表")
    return data


def _write_json_models(file_path: Path, models: list[Garden | PlantingRecord]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = file_path.with_name(f"{file_path.name}.tmp")
    data = [model.model_dump(mode="json") for model in models]
    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        temporary_file.replace(file_path)
    finally:
        temporary_file.unlink(missing_ok=True)


def _normalize_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError("UUID 格式无效。") from error

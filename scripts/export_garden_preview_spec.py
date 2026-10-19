"""为 Step 9 PixiJS 花园预览导出真实 GardenRenderSpec fixture。"""

import json
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from flower_engine import (
    FlowerSpec,
    Garden,
    PlantingRecord,
    build_flower_render_spec,
    build_flower_variation,
    create_flower_artifact,
    garden_to_render_spec,
    get_flower_reference,
)


OUTPUT_PATH = PROJECT_ROOT / "development" / "demo" / "creation_preview" / "public" / "garden-preview-spec.json"

FLOWERS = (
    ("rose", 2, 2, 0.70, 9101),
    ("peony", 6, 2, 0.92, 9102),
    ("sunflower", 11, 1, 1.00, 9103),
    ("tulip", 14, 3, 0.58, 9104),
    ("hydrangea", 4, 5, 0.82, 9105),
    ("lily", 9, 4, 0.66, 9106),
    ("daisy", 1, 7, 0.45, 9107),
    ("lavender", 7, 7, 0.74, 9108),
    ("wildflower", 13, 7, 0.55, 9109),
)


def build_preview_domain() -> tuple[Garden, list, list[PlantingRecord]]:
    garden = Garden(
        id=uuid5(NAMESPACE_URL, "musegarden:step9:garden"),
        name="MuseGarden Preview",
        width=16,
        height=10,
    )
    artifacts = []
    plantings = []

    for index, (species, x, y, size, seed) in enumerate(FLOWERS):
        reference = get_flower_reference(species)
        flower_spec = FlowerSpec(
            species=species,
            palette=reference.supported_palettes[0],
            size=size,
            petal_count=reference.base_petal_count,
            stem_height=reference.base_stem_height,
            sway_speed=round(0.28 + index * 0.065, 3),
            glow=round(0.25 + index * 0.06, 3),
            particle_effect="sparkles" if index % 3 == 0 else "soft_glow",
            decoration=reference.supported_decorations[
                min(1, len(reference.supported_decorations) - 1)
            ],
            growth_direction="rising" if index % 2 == 0 else "opening",
        )
        variation = build_flower_variation(flower_spec, seed)
        render_spec = build_flower_render_spec(flower_spec, variation)
        artifact = create_flower_artifact(flower_spec, render_spec).model_copy(
            update={
                "id": uuid5(NAMESPACE_URL, f"musegarden:step9:flower:{species}")
            },
            deep=True,
        )
        artifacts.append(artifact)
        plantings.append(
            PlantingRecord(
                id=uuid5(NAMESPACE_URL, f"musegarden:step9:planting:{species}"),
                garden_id=garden.id,
                flower_artifact_id=artifact.id,
                x=x,
                y=y,
            )
        )

    return garden, artifacts, plantings


def build_preview_spec() -> dict:
    garden, artifacts, plantings = build_preview_domain()
    return garden_to_render_spec(
        garden,
        plantings,
        artifacts,
    ).model_dump(mode="json")


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(build_preview_spec(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Garden preview fixture exported: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

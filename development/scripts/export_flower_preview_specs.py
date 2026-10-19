"""为 Step 5 PixiJS 预览导出由真实 Flower Engine 生成的 RenderSpec fixture。"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from flower_engine import (
    FlowerSpec,
    build_flower_render_spec,
    build_flower_variation,
    get_flower_reference,
)


OUTPUT_PATH = PROJECT_ROOT / "development" / "demo" / "creation_preview" / "public" / "flower-preview-specs.json"

SPECIES = (
    "rose", "peony", "sunflower", "tulip", "hydrangea",
    "lily", "daisy", "lavender", "wildflower",
)

EFFECTS = (
    "petals", "sparkles", "fireflies", "soft_glow", "stardust",
    "sparkles", "none", "fireflies", "stardust",
)


def build_preview_groups() -> list[dict]:
    groups = []
    for species_index, species in enumerate(SPECIES):
        reference = get_flower_reference(species)
        spec = FlowerSpec(
            species=species,
            palette=reference.supported_palettes[0],
            size=round(0.58 + species_index * 0.035, 2),
            petal_count=reference.base_petal_count,
            stem_height=reference.base_stem_height,
            sway_speed=round(0.30 + species_index * 0.06, 2),
            glow=round(0.28 + species_index * 0.055, 2),
            particle_effect=EFFECTS[species_index],
            decoration=reference.supported_decorations[
                min(1, len(reference.supported_decorations) - 1)
            ],
            growth_direction="rising" if species_index % 2 == 0 else "opening",
        )
        variants = []
        for variant_index in range(3):
            seed = 5100 + species_index * 10 + variant_index
            variation = build_flower_variation(spec, seed)
            variants.append(
                build_flower_render_spec(spec, variation).model_dump(mode="json")
            )
        groups.append(
            {
                "species": species,
                "display_name": reference.display_name,
                "variants": variants,
            }
        )
    return groups


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(build_preview_groups(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Flower preview fixtures exported: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

# Mini Meadow Asset Index

## Provenance and licence

- **Pack:** Mini Meadow — 16×16 Pixel-Art Tileset
- **Author:** myobln
- **Official page:** https://myobln.itch.io/game-assets
- **Licence:** CC0-1.0 (public domain)
- **Downloaded:** 2026-10-25
- **Original archive:** `mini_meadow_upload_bundle.zip` (65,675 bytes)
- **SHA-256:** `608ba6d099c4f8aedf363afc7e483f996c9c4c03d1672dfa4f0b43739d0a5674`

The original `README.md` and `manifest.json` remain under `unpacked/mini_meadow/`.

## Validation

- ZIP directory was checked before extraction: no rooted paths or `..` traversal entries.
- `manifest.json` contains 75 tiles; every referenced file exists.
- 86 PNG files are present: 75 individual tiles, 9 sheets, and 2 supplied previews.
- Individual tiles are 16×16 RGBA PNGs. Composite sheets use RGBA; supplied previews are RGB.

## Files

| Location | Size / contents | Use |
| --- | --- | --- |
| `unpacked/mini_meadow/tiles/` | 75 individual 16×16 RGBA tiles | Preferred source for explicit Pixi texture mapping. |
| `sheets/ground.png` | 144×16 | 9 ground tiles in one row: grass, dirt, sand, stone and four water frames. |
| `sheets/edges_grass_dirt.png` | 128×16 | Eight grass↔dirt orientations. |
| `sheets/edges_grass_sand.png` | 128×16 | Eight grass↔sand orientations. |
| `sheets/edges_grass_stone.png` | 128×16 | Eight grass↔stone orientations. |
| `sheets/edges_grass_water_f1..f4.png` | 128×16 each | Eight grass↔water orientations for each water frame. |
| `sheets/props.png` | 160×16 | Ten transparent props. |
| `preview/atlas.png` | 640×704 | Supplied full inventory preview, nearest-neighbour pixel art. |
| `preview/scene.png` | 640×480 | Supplied assembled example scene. |
| `zip-file-list.csv` | archive inventory | Reproducible ZIP file listing. |

## Tile groups

| Group | IDs / count | MuseGarden fit |
| --- | --- | --- |
| Grass | `grass_a`, `grass_b` | Strong fit for `GRASS`; use `grass_a` as base and deterministic/sparse `grass_b` variation. |
| Dirt | `dirt` | Suitable candidate for `PATH` and potentially `SOIL`; it is the pack's only cultivated-earth-like surface. Keep current SOIL logic untouched until visual design decides how to distinguish paths and fields. |
| Water | `water_1` through `water_4` | Strong fit for `WATER`; four distinct animation frames. |
| Grass-water shoreline | 32 tiles: 8 orientations × 4 frames | Strong fit for later river-bank transitions. Confirm exact frame synchronization during the water-animation step. |
| Grass-dirt edges | 8 orientations | Suitable for road / field borders. |
| Grass-sand and grass-stone edges | 16 tiles | Useful later for plazas, banks or rocky edges; not presently required. |
| Props | flowers, mushrooms, rock, pebbles, tuft, bush, log, stump | Useful later as decoration. Keep separate from memory flowers so generated flowers retain their own gameplay identity. |

## Current terrain mapping recommendation

| Current terrain | Proposed material | Status |
| --- | --- | --- |
| `GRASS` | `grass_a` + limited `grass_b` variation | First replacement candidate in Step 16.1. |
| `SOIL` | `dirt`, with grass-dirt edges considered later | Available, but defer to retain clear gameplay fields. |
| `PATH` | `dirt`, optionally grass-dirt edges | Available, but defer. |
| `WATER` | `water_1..4`; grass-water edges | Available, but defer. |
| `BRIDGE` | No bridge tile supplied | Keep current rendering until a dedicated bridge asset exists. |
| `STRUCTURE` | No building tile supplied | Keep current rendering until a building asset set is selected. |

## Recommended Pixi integration

Keep the raw source in this third-party directory. In Step 16.1, copy only the selected runtime texture(s) into `frontend/src/assets/third-party/mini-meadow/` or load them from a deliberate public-assets path. Create `Texture` objects with nearest-neighbour scale mode, cache them once in `TerrainRenderer`, and select them from existing terrain data. Do not resize source images, rebuild the map, or create a React element per terrain cell.

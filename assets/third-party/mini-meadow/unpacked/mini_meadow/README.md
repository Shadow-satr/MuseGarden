# Mini Meadow — 16×16 Top-Down Nature Tileset (CC0)

Free CC0 pixel-art tileset for top-down / RPG / cozy-game prototyping.
All tiles are 16×16 PNGs (RGBA). **No generative-AI models were used** —
every pixel is produced by original deterministic code (seeded procedural
drawing). Full commercial use allowed, no credit required (appreciated).

## Contents (75 tiles)
- Ground (seamless, tileable): grass_a, grass_b, dirt, sand, stone,
  water_1..water_4 — 4-frame animation loop. Water bands are 4px-periodic
  and aligned to the tile grid, so cycling the frames animates the whole
  sheet without seams.
- Autotile edge tiles, 8 orientations each (N/S/E/W/NE/NW/SE/SW, where the
  first material occupies that side/quadrant), with a crisp 1px dark
  outline at the boundary:
  - edge_grass_dirt_* (paths)
  - edge_grass_sand_*
  - edge_grass_stone_*
  - edge_grass_water_*_f1..f4 — animated shores: cycle the shore tiles in
    lockstep with the matching water frame (same _fN suffix) so the bands
    stay continuous between shore and open water
- Props (transparent background): flower_pink, flower_white, mushroom_red,
  mushroom_brown, rock, pebbles, tuft, bush, log, stump

## Files
- tiles/ — one PNG per tile (75 files)
- sheets/ground.png — ground tiles in one row
- sheets/edges_<pair>.png — 8 edge tiles per pair (water shores: one sheet
  per animation frame, edges_grass_water_f1..f4)
- sheets/props.png — all props in one row
- preview/scene.png — example map assembled from the tiles
- preview/atlas.png — full inventory sheet
- manifest.json — machine-readable index (id/file/desc)

## Palette
Outline #1E1C28 · Grass #60A84A / #80C862 / #427E32 · Dirt #AC7C50 / #C8986A /
#845A36 · Sand #D8BE8C / #EED8AA / #B09666 · Stone #9096A2 / #B4BACC / #6A7080 ·
Water #466CB8 / #6496E0 / #304C92 (deep) / #C8E4FA (sparkle)

## Notes
- Ground tiles keep a flat 1px base-colour ring so identical tiles sit
  seamlessly next to each other.
- Water edge (shore) tiles are static — animate the water_1..4 interior
  tiles only.
- License: CC0-1.0 (public domain). No attribution required.

# Step 16.6.1 — Environmental Decoration Plan

## Scope

This is a **development-only planning preview**. It imports the real `MUSE_GARDEN_TERRAIN` data at generation time, but it does not alter the runtime map, renderer, assets, collision rules, or planting system. Yellow dashed cells are suggested placements; pink dashed cells are SOIL and must remain free for memory flowers.

## Actual candidate assets

| Asset | Actual source | Recommendation | Rule |
| --- | --- | --- | --- |
| `bush.png` | 16×16 RGBA, transparent | Recommended | Sparse edge and building-side anchor; grass only; 1-cell clear margin. |
| `rock.png` | 16×16 RGBA, transparent | Recommended | Single accent in quiet grass; do not form rows. |
| `pebbles.png` | 16×16 RGBA, transparent | Optional | At most a few, never a ground texture. |
| `log.png`, `stump.png` | 16×16 RGBA, transparent | Optional | Use one or the other at a remote edge; decide collision before runtime use. |
| `mushroom_brown.png` | 16×16 RGBA, transparent | Optional | Rare low accent; grass only. |
| `mushroom_red.png` | 16×16 RGBA, transparent | Exclude | Too saturated; competes with gameplay memory flowers. |
| `flower_pink.png`, `flower_white.png` | 16×16 RGBA, transparent | Exclude | Must not be confused with planted memory flowers. |
| `tuft.png` | 16×16 RGBA, transparent | Exclude | User previously rejected it; do not reintroduce. |

No tree asset exists in this pack. Large trees are therefore deliberately **not** represented in the preview. A later Step 16.7 may use bushes as the low-impact first runtime decoration, or source a coherent tree asset only after approval.

## Layout rules

- Use only GRASS cells with a one-cell all-GRASS clearance; never decorate SOIL, PATH, WATER, BRIDGE, or STRUCTURE.
- Keep all bridge heads, road entrances, field approaches, and river banks clear.
- The plan is intentionally sparse: 25 suggested cells (bush: 7, rock: 7, pebbles: 5, log: 2, stump: 2, mushroom_brown: 2).
- Props are cosmetic in this plan. Bushes/logs/stumps may need collision if used as future navigation blockers; do not imply collision before a dedicated movement decision.

## Files

- `environment-decoration-layout-preview.svg` — full map from actual TerrainMap data plus proposed props.
- `environment-decoration-candidates.svg` — enlarged candidate comparison using source PNG transparency.

Generated with `generateDecorationLayoutPreview.ts`.

/**
 * Development-only Step 16.6.1 preview generator.
 * Bundled with esbuild before execution so it reads the real TerrainMap module,
 * but it is never imported by the frontend runtime.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { TERRAIN_COLORS } from "../../frontend/src/world/TerrainColors";
import { MUSE_GARDEN_TERRAIN, type TerrainType } from "../../frontend/src/world/TerrainMap";

const directory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(directory, "../..");
const outputSvg = resolve(directory, "environment-decoration-layout-preview.svg");
const outputIndex = resolve(directory, "environment-decoration-candidates.svg");
const outputNotes = resolve(directory, "environment-decoration-plan.md");
const sourceTiles = resolve(repositoryRoot, "assets/third-party/mini-meadow/unpacked/mini_meadow/tiles");
const cell = MUSE_GARDEN_TERRAIN.cellSize;

type DecorKind = "bush" | "rock" | "pebbles" | "log" | "stump" | "mushroom_brown" | "mushroom_red";
interface PlannedDecoration { readonly kind: DecorKind; readonly column: number; readonly row: number; }

const candidates: Record<DecorKind, { readonly label: string; readonly use: string; readonly avoid: string }> = {
  bush: { label: "灌木", use: "推荐：地图边缘、建筑侧后方；作为环境骨架", avoid: "道路、桥头、田地入口、水岸" },
  rock: { label: "岩石", use: "推荐：开阔草地的单点停顿", avoid: "路径边缘、玩家主通路" },
  pebbles: { label: "碎石", use: "候选：极少量建筑附近或草地角落", avoid: "不要铺成重复底纹" },
  log: { label: "原木", use: "候选：远离主路的边缘草地", avoid: "若将来无碰撞，避免放在显眼通路" },
  stump: { label: "树桩", use: "候选：与原木二选一的边缘叙事点", avoid: "不要和灌木并排成装饰墙" },
  mushroom_brown: { label: "棕蘑菇", use: "候选：只作极少量低矮点缀", avoid: "田地、道路、桥头" },
  mushroom_red: { label: "红蘑菇", use: "排除：颜色过强，容易抢走记忆花朵注意力", avoid: "本轮不建议使用" },
};

function terrainAt(column: number, row: number): TerrainType {
  return MUSE_GARDEN_TERRAIN.terrainAt(column, row);
}

/** A proposed prop must stay on clear grass and away from all gameplay areas. */
function hasClearGrass(column: number, row: number, clearance = 1): boolean {
  for (let y = row - clearance; y <= row + clearance; y += 1) {
    for (let x = column - clearance; x <= column + clearance; x += 1) {
      if (terrainAt(x, y) !== "GRASS") return false;
    }
  }
  return true;
}

function pick(kind: DecorKind, options: readonly (readonly [number, number])[], clearance = 1): PlannedDecoration[] {
  const selected: PlannedDecoration[] = [];
  for (const [column, row] of options) {
    if (!hasClearGrass(column, row, clearance)) continue;
    if (selected.some((entry) => Math.abs(entry.column - column) + Math.abs(entry.row - row) < 5)) continue;
    selected.push({ kind, column, row });
  }
  return selected;
}

// Intentional sparse layout: edge anchors first, then a few quiet small accents.
const plan: readonly PlannedDecoration[] = [
  ...pick("bush", [[18, 6], [29, 7], [58, 5], [74, 7], [76, 23], [76, 48], [69, 54], [37, 54], [17, 50], [17, 18]], 1),
  ...pick("rock", [[18, 12], [31, 14], [59, 23], [75, 36], [70, 52], [37, 52], [18, 45], [16, 25]], 1),
  ...pick("pebbles", [[34, 10], [59, 9], [72, 19], [74, 53], [32, 51], [16, 40]], 1),
  ...pick("log", [[13, 14], [78, 42], [33, 57]], 1),
  ...pick("stump", [[17, 10], [73, 29], [17, 54]], 1),
  ...pick("mushroom_brown", [[22, 9], [72, 24], [75, 50], [20, 48]], 1),
];

function base64Tile(kind: DecorKind): string {
  return readFileSync(resolve(sourceTiles, `${kind}.png`)).toString("base64");
}

function svgImage(kind: DecorKind, column: number, row: number, scale = 1): string {
  const size = cell * scale;
  const href = `data:image/png;base64,${base64Tile(kind)}`;
  return `<image href="${href}" x="${column * cell}" y="${row * cell}" width="${size}" height="${size}" image-rendering="pixelated" />`;
}

function svgTerrain(): string {
  return [...MUSE_GARDEN_TERRAIN.entries()].map(({ column, row, terrain }) =>
    `<rect x="${column * cell}" y="${row * cell}" width="${cell}" height="${cell}" fill="${TERRAIN_COLORS[terrain]}" />`,
  ).join("");
}

function forbiddenSoilOverlay(): string {
  return [...MUSE_GARDEN_TERRAIN.entries()]
    .filter((entry) => entry.terrain === "SOIL")
    .map(({ column, row }) => `<rect x="${column * cell + 2}" y="${row * cell + 2}" width="${cell - 4}" height="${cell - 4}" fill="none" stroke="#f0c7b4" stroke-width="1" stroke-dasharray="3 2" opacity="0.75" />`)
    .join("");
}

function makeLayoutSvg(): string {
  const proposed = plan.map(({ kind, column, row }) => {
    const x = column * cell;
    const y = row * cell;
    return `<rect x="${x - 1}" y="${y - 1}" width="${cell + 2}" height="${cell + 2}" fill="none" stroke="#f8e7a4" stroke-width="1" stroke-dasharray="3 2" />${svgImage(kind, column, row)}`;
  }).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${MUSE_GARDEN_TERRAIN.width}" height="${MUSE_GARDEN_TERRAIN.height}" viewBox="0 0 ${MUSE_GARDEN_TERRAIN.width} ${MUSE_GARDEN_TERRAIN.height}">
<title>MuseGarden environmental decoration layout preview</title>
<rect width="100%" height="100%" fill="#16241d" />${svgTerrain()}${forbiddenSoilOverlay()}${proposed}
<g font-family="monospace" font-size="24" fill="#fff4d4" stroke="#16241d" stroke-width="5" paint-order="stroke"><text x="24" y="38">STEP 16.6.1 · PROPOSED DECORATION LAYOUT</text><text x="24" y="68">yellow dashed = proposed prop · pink dashed = soil / no decoration</text></g>
</svg>`;
}

function makeCandidateSvg(): string {
  const kinds = Object.keys(candidates) as DecorKind[];
  const rowHeight = 112;
  const width = 1040;
  const entries = kinds.map((kind, index) => {
    const y = 20 + index * rowHeight;
    const asset = svgImage(kind, 0, 0, 4).replace('x="0" y="0"', `x="28" y="${y}"`);
    const detail = candidates[kind];
    return `<rect x="12" y="${y - 8}" width="${width - 24}" height="96" rx="8" fill="#24382d" stroke="#526b58" />${asset}<text x="120" y="${y + 26}" fill="#fff1ca" font-family="sans-serif" font-size="24">${detail.label} · ${kind}</text><text x="120" y="${y + 52}" fill="#d5dfcf" font-family="sans-serif" font-size="16">${detail.use}</text><text x="120" y="${y + 75}" fill="#b6c0b2" font-family="sans-serif" font-size="15">避免：${detail.avoid}</text>`;
  }).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${kinds.length * rowHeight + 32}" viewBox="0 0 ${width} ${kinds.length * rowHeight + 32}"><rect width="100%" height="100%" fill="#13221a" /><text x="22" y="28" fill="#fff4d4" font-family="monospace" font-size="18">Mini Meadow · decoration candidates (nearest-neighbour 4×)</text>${entries}</svg>`;
}

function makeNotes(): string {
  const counts = plan.reduce<Record<string, number>>((result, entry) => ({ ...result, [entry.kind]: (result[entry.kind] ?? 0) + 1 }), {});
  return `# Step 16.6.1 — Environmental Decoration Plan\n\n## Scope\n\nThis is a **development-only planning preview**. It imports the real \`MUSE_GARDEN_TERRAIN\` data at generation time, but it does not alter the runtime map, renderer, assets, collision rules, or planting system. Yellow dashed cells are suggested placements; pink dashed cells are SOIL and must remain free for memory flowers.\n\n## Actual candidate assets\n\n| Asset | Actual source | Recommendation | Rule |\n| --- | --- | --- | --- |\n| \`bush.png\` | 16×16 RGBA, transparent | Recommended | Sparse edge and building-side anchor; grass only; 1-cell clear margin. |\n| \`rock.png\` | 16×16 RGBA, transparent | Recommended | Single accent in quiet grass; do not form rows. |\n| \`pebbles.png\` | 16×16 RGBA, transparent | Optional | At most a few, never a ground texture. |\n| \`log.png\`, \`stump.png\` | 16×16 RGBA, transparent | Optional | Use one or the other at a remote edge; decide collision before runtime use. |\n| \`mushroom_brown.png\` | 16×16 RGBA, transparent | Optional | Rare low accent; grass only. |\n| \`mushroom_red.png\` | 16×16 RGBA, transparent | Exclude | Too saturated; competes with gameplay memory flowers. |\n| \`flower_pink.png\`, \`flower_white.png\` | 16×16 RGBA, transparent | Exclude | Must not be confused with planted memory flowers. |\n| \`tuft.png\` | 16×16 RGBA, transparent | Exclude | User previously rejected it; do not reintroduce. |\n\nNo tree asset exists in this pack. Large trees are therefore deliberately **not** represented in the preview. A later Step 16.7 may use bushes as the low-impact first runtime decoration, or source a coherent tree asset only after approval.\n\n## Layout rules\n\n- Use only GRASS cells with a one-cell all-GRASS clearance; never decorate SOIL, PATH, WATER, BRIDGE, or STRUCTURE.\n- Keep all bridge heads, road entrances, field approaches, and river banks clear.\n- The plan is intentionally sparse: ${plan.length} suggested cells (${Object.entries(counts).map(([kind, count]) => `${kind}: ${count}`).join(", ")}).\n- Props are cosmetic in this plan. Bushes/logs/stumps may need collision if used as future navigation blockers; do not imply collision before a dedicated movement decision.\n\n## Files\n\n- \`environment-decoration-layout-preview.svg\` — full map from actual TerrainMap data plus proposed props.\n- \`environment-decoration-candidates.svg\` — enlarged candidate comparison using source PNG transparency.\n\nGenerated with \`generateDecorationLayoutPreview.ts\`.\n`;
}

writeFileSync(outputSvg, makeLayoutSvg(), "utf8");
writeFileSync(outputIndex, makeCandidateSvg(), "utf8");
writeFileSync(outputNotes, makeNotes(), "utf8");
console.log(`Generated ${outputSvg}`);
console.log(`Generated ${outputIndex}`);
console.log(`Generated ${outputNotes}`);

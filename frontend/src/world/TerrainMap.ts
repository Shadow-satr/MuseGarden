/** The design reference is 1448 × 1086; gameplay keeps those world bounds. */
export const WORLD_WIDTH = 1448;
export const WORLD_HEIGHT = 1086;
export const TERRAIN_CELL_SIZE = 16;
export const TERRAIN_COLUMNS = Math.ceil(WORLD_WIDTH / TERRAIN_CELL_SIZE);
export const TERRAIN_ROWS = Math.ceil(WORLD_HEIGHT / TERRAIN_CELL_SIZE);

export type TerrainType = "GRASS" | "PATH" | "WATER" | "SOIL" | "STRUCTURE" | "BRIDGE" | "TREE";

export interface TerrainMap {
  readonly width: number;
  readonly height: number;
  readonly cellSize: number;
  terrainAt(column: number, row: number): TerrainType;
  entries(): Iterable<{ column: number; row: number; terrain: TerrainType }>;
}

export interface FarmSlot {
  readonly plotId: string;
  readonly slot: number;
  readonly column: number;
  readonly row: number;
  readonly width: number;
  readonly height: number;
  readonly centerX: number;
  readonly centerY: number;
}

export interface FarmPlot {
  readonly id: string;
  readonly slots: readonly FarmSlot[];
}

class MutableTerrainMap implements TerrainMap {
  readonly width = WORLD_WIDTH;
  readonly height = WORLD_HEIGHT;
  readonly cellSize = TERRAIN_CELL_SIZE;
  private readonly cells = new Array<TerrainType>(TERRAIN_COLUMNS * TERRAIN_ROWS).fill("GRASS");

  terrainAt(column: number, row: number): TerrainType {
    if (column < 0 || row < 0 || column >= TERRAIN_COLUMNS || row >= TERRAIN_ROWS) return "WATER";
    return this.cells[row * TERRAIN_COLUMNS + column];
  }

  paint(column: number, row: number, width: number, height: number, terrain: TerrainType): void {
    const right = Math.min(TERRAIN_COLUMNS, column + width);
    const bottom = Math.min(TERRAIN_ROWS, row + height);
    for (let y = Math.max(0, row); y < bottom; y += 1) {
      for (let x = Math.max(0, column); x < right; x += 1) {
        this.cells[y * TERRAIN_COLUMNS + x] = terrain;
      }
    }
  }

  *entries(): Iterable<{ column: number; row: number; terrain: TerrainType }> {
    for (let row = 0; row < TERRAIN_ROWS; row += 1) {
      for (let column = 0; column < TERRAIN_COLUMNS; column += 1) {
        yield { column, row, terrain: this.terrainAt(column, row) };
      }
    }
  }
}

const FARM_SLOT_WIDTH = 4;
const FARM_SLOT_HEIGHT = 4;
const FARM_SLOT_GAP = 1;

function createFarmPlot(id: string, column: number, row: number): FarmPlot {
  const slots: FarmSlot[] = [];
  for (let slotRow = 0; slotRow < 2; slotRow += 1) {
    for (let slotColumn = 0; slotColumn < 3; slotColumn += 1) {
      const slot = slotRow * 3 + slotColumn;
      const slotX = column + slotColumn * (FARM_SLOT_WIDTH + FARM_SLOT_GAP);
      const slotY = row + slotRow * (FARM_SLOT_HEIGHT + FARM_SLOT_GAP);
      slots.push({
        plotId: id,
        slot,
        column: slotX,
        row: slotY,
        width: FARM_SLOT_WIDTH,
        height: FARM_SLOT_HEIGHT,
        centerX: (slotX + FARM_SLOT_WIDTH / 2) * TERRAIN_CELL_SIZE,
        centerY: (slotY + FARM_SLOT_HEIGHT / 2) * TERRAIN_CELL_SIZE,
      });
    }
  }
  return { id, slots };
}

/** Four 3 × 2 fields, ordered top-left, top-right, bottom-left, bottom-right. */
export const FARM_PLOTS: readonly FarmPlot[] = [
  createFarmPlot("north-west", 21, 17),
  createFarmPlot("north-east", 62, 18),
  createFarmPlot("south-west", 21, 41),
  createFarmPlot("south-east", 57, 41),
];

/** These two fields are continuous soil beds; the other fields keep visible slot gaps. */
export const MERGED_FARM_PLOT_IDS = new Set(["north-west", "south-east"]);

function paintFarm(map: MutableTerrainMap, plot: FarmPlot): void {
  if (MERGED_FARM_PLOT_IDS.has(plot.id)) {
    const first = plot.slots[0];
    map.paint(first.column, first.row, 14, 9, "SOIL");
    return;
  }
  for (const slot of plot.slots) map.paint(slot.column, slot.row, slot.width, slot.height, "SOIL");
}

/** Grid-based layout V1, traced from grid-map-layout-v1-reference.png. */
export function createMuseGardenTerrain(): TerrainMap {
  const map = new MutableTerrainMap();

  // Curved western river.
  for (const [row, column, width, height] of [
    [0, 3, 11, 3], [3, 4, 11, 3], [6, 7, 9, 5], [11, 8, 8, 5],
    [16, 7, 8, 5], [21, 5, 9, 5], [26, 3, 10, 7], [33, 4, 10, 8],
    [41, 5, 10, 7], [48, 7, 11, 6], [54, 9, 14, 4],
  ] as const) map.paint(column, row, width, height, "WATER");

  // Water frames the island along the south and curls up the east edge.
  // The southern band is eight cells deep across the full map.
  map.paint(0, 60, TERRAIN_COLUMNS, TERRAIN_ROWS - 60, "WATER");
  map.paint(84, 38, TERRAIN_COLUMNS - 84, 30, "WATER");
  map.paint(81, 45, 10, 15, "WATER");
  // Continue the western river through the south-west shore without a grass gap.
  map.paint(9, 54, 14, 7, "WATER");

  // Leave a one-cell grass bank above the west bridge approach.
  map.paint(3, 30, 1, 1, "GRASS");

  // Connected road network: main crossroad, building approaches and farm loops.
  map.paint(14, 31, 68, 4, "PATH");
  map.paint(43, 28, 8, 9, "PATH");
  map.paint(45, 12, 4, 18, "PATH");
  map.paint(45, 34, 4, 25, "PATH");
  map.paint(48, 17, 12, 3, "PATH");
  map.paint(58, 15, 3, 6, "PATH");
  map.paint(60, 14, 9, 3, "PATH");
  map.paint(68, 12, 3, 5, "PATH");
  map.paint(26, 26, 4, 7, "PATH");
  map.paint(67, 27, 4, 6, "PATH");
  map.paint(26, 35, 4, 7, "PATH");
  map.paint(62, 35, 4, 7, "PATH");
  map.paint(26, 50, 4, 5, "PATH");
  map.paint(26, 53, 40, 3, "PATH");
  map.paint(62, 50, 4, 6, "PATH");

  // NW and SE are continuous beds; NE and SW retain the six separated soil patches.
  for (const plot of FARM_PLOTS) paintFarm(map, plot);

  // Main building and auxiliary building footprints at the north of the island.
  map.paint(41, 6, 15, 9, "STRUCTURE");
  map.paint(64, 6, 9, 8, "STRUCTURE");

  // Bridges override water and align with connected paths.
  map.paint(0, 31, 4, 4, "PATH");
  map.paint(4, 31, 9, 4, "BRIDGE");
  map.paint(13, 31, 1, 4, "PATH");
  // A narrow east-bank strip keeps the west-bridge road corner off open water.
  map.paint(13, 35, 1, 3, "GRASS");
  map.paint(45, 59, 4, 1, "PATH");
  map.paint(45, 60, 4, 8, "BRIDGE");

  // Planted groves are real world obstacles, not decorative overlays. Their
  // footprints deliberately sit on spare grass so they do not cover paths,
  // water, fields, or building entrances.
  for (const [column, row, width, height] of [
    // Isolated saplings, medium trees, and contiguous groves intentionally vary in scale.
    [17, 6, 1, 1], [20, 8, 2, 2], [31, 7, 3, 2], [75, 13, 2, 2],
    [74, 27, 1, 1], [77, 27, 2, 3], [17, 44, 1, 1], [19, 46, 2, 2],
    [73, 43, 3, 3], [72, 53, 1, 1], [75, 53, 3, 3],
  ] as const) map.paint(column, row, width, height, "TREE");

  return map;
}

export const MUSE_GARDEN_TERRAIN = createMuseGardenTerrain();

// Keep the rendering footprints as layout regions, while collision follows the
// visible silhouettes inside them instead of blocking their empty corners.
const OBSTACLE_REGIONS = [
  { type: "STRUCTURE", column: 41, row: 6, width: 15, height: 9 },
  { type: "STRUCTURE", column: 64, row: 6, width: 9, height: 8 },
  ...[[17, 6, 1, 1], [20, 8, 2, 2], [31, 7, 3, 2], [75, 13, 2, 2],
    [74, 27, 1, 1], [77, 27, 2, 3], [17, 44, 1, 1], [19, 46, 2, 2],
    [73, 43, 3, 3], [72, 53, 1, 1], [75, 53, 3, 3]].map(([column, row, width, height]) => ({ type: "TREE", column, row, width, height })),
] as const;

export function treeShapes(column: number, row: number, columns: number, rows: number) {
  const width = columns * 16, height = rows * 16;
  const hash = (Math.imul(column + 17, 1103515245) ^ Math.imul(row + 31, 12345)) >>> 0;
  const trees = hash % 3 === 1 && columns >= 3 && rows >= 2
    ? [[width * .32, height * .86, .9], [width * .68, height * .9, 1.05]]
    : [[width / 2, height * .88, Math.min(width, height) / 16]];
  return trees.map(([x, y, scale]) => ({ x: column * 16 + x, rootY: row * 16 + y, radius: Math.min(width * .43, height * .37, 16 * .38 * scale) }));
}

export function terrainAtWorldPosition(x: number, y: number): TerrainType {
  return MUSE_GARDEN_TERRAIN.terrainAt(
    Math.floor(x / TERRAIN_CELL_SIZE),
    Math.floor(y / TERRAIN_CELL_SIZE),
  );
}

export function isWalkableWorldPosition(x: number, y: number): boolean {
  for (const region of OBSTACLE_REGIONS) {
    if (region.type !== "TREE") continue;
    for (const tree of treeShapes(region.column, region.row, region.width, region.height)) {
      const crownY = tree.rootY - tree.radius * 1.05;
      const circles = [[tree.x - tree.radius * .46, crownY + tree.radius * .34, tree.radius * .68],
        [tree.x + tree.radius * .46, crownY + tree.radius * .36, tree.radius * .66],
        [tree.x, crownY, tree.radius * .83]];
      if (circles.some(([cx, cy, radius]) => (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2)) return false;
      if (Math.abs(x - tree.x) <= Math.max(2, tree.radius * .25) && y >= crownY && y <= tree.rootY) return false;
    }
  }
  const terrain = terrainAtWorldPosition(x, y);
  if (terrain === "WATER") return false;
  if (terrain === "TREE") return true;
  if (terrain !== "STRUCTURE") return true;
  const region = OBSTACLE_REGIONS.find((item) => item.type === terrain && x >= item.column * 16 && x < (item.column + item.width) * 16 && y >= item.row * 16 && y < (item.row + item.height) * 16);
  if (!region) return false;
  const localX = x - region.column * 16;
  const localY = y - region.row * 16;
  const width = region.width * 16;
  const height = region.height * 16;
  if (terrain === "STRUCTURE") {
    const roofBottom = Math.floor(height * .57);
    if (localY >= roofBottom - 2) return !(localX >= 3 && localX < width - 3 && localY < height - 3);
    const tierHeight = Math.max(4, Math.floor((roofBottom - 4) / 5));
    const tier = Math.floor((localY - 3) / tierHeight);
    if (tier < 0 || tier >= 5) return true;
    const inset = Math.max(4, Math.floor(width * (.09 + (4 - tier) * .055)));
    return localX < inset || localX >= width - inset;
  }
  return true;
}

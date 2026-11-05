import { describe, expect, it } from "vitest";

import {
  MUSE_GARDEN_TERRAIN,
  FARM_PLOTS,
  MERGED_FARM_PLOT_IDS,
  TERRAIN_CELL_SIZE,
  TERRAIN_COLUMNS,
  TERRAIN_ROWS,
  WORLD_HEIGHT,
  WORLD_WIDTH,
  isWalkableWorldPosition,
  type TerrainType,
} from "./TerrainMap";

describe("Grid terrain map", () => {
  it("keeps the formal world dimensions on a 16px grid", () => {
    expect(MUSE_GARDEN_TERRAIN.width).toBe(WORLD_WIDTH);
    expect(MUSE_GARDEN_TERRAIN.height).toBe(WORLD_HEIGHT);
    expect(MUSE_GARDEN_TERRAIN.cellSize).toBe(TERRAIN_CELL_SIZE);
    expect(TERRAIN_COLUMNS * TERRAIN_CELL_SIZE).toBeGreaterThanOrEqual(WORLD_WIDTH);
    expect(TERRAIN_ROWS * TERRAIN_CELL_SIZE).toBeGreaterThanOrEqual(WORLD_HEIGHT);
  });

  it("classifies every cell and includes every Step 13 terrain type", () => {
    const seen = new Set<TerrainType>();
    let count = 0;
    for (const entry of MUSE_GARDEN_TERRAIN.entries()) {
      seen.add(entry.terrain);
      count += 1;
    }
    expect(count).toBe(TERRAIN_COLUMNS * TERRAIN_ROWS);
    expect(seen).toEqual(new Set<TerrainType>(["GRASS", "PATH", "WATER", "SOIL", "STRUCTURE", "BRIDGE", "TREE"]));
  });

  it("keeps NW and SE continuous while the other fields retain six soil patches", () => {
    expect(FARM_PLOTS).toHaveLength(4);
    for (const plot of FARM_PLOTS) {
      expect(plot.slots).toHaveLength(6);
      for (const slot of plot.slots) {
        expect(MUSE_GARDEN_TERRAIN.terrainAt(slot.column, slot.row)).toBe("SOIL");
        expect(MUSE_GARDEN_TERRAIN.terrainAt(slot.column + slot.width - 1, slot.row + slot.height - 1)).toBe("SOIL");
      }
      const formerGap = MUSE_GARDEN_TERRAIN.terrainAt(plot.slots[0].column + 4, plot.slots[0].row);
      if (MERGED_FARM_PLOT_IDS.has(plot.id)) expect(formerGap).toBe("SOIL");
      else expect(formerGap).not.toBe("SOIL");
    }
  });

  it("keeps water, structures and tree groves blocked while paths, bridges and soil are walkable", () => {
    expect(MUSE_GARDEN_TERRAIN.terrainAt(3, 0)).toBe("WATER");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(46, 60)).toBe("BRIDGE");
    expect(isWalkableWorldPosition(3 * 16 + 8, 8)).toBe(false);
    expect(isWalkableWorldPosition(48 * 16 + 8, 7 * 16 + 8)).toBe(false);
    expect(isWalkableWorldPosition(41 * 16 + 2, 6 * 16 + 2)).toBe(true);
    expect(MUSE_GARDEN_TERRAIN.terrainAt(17, 6)).toBe("TREE");
    expect(isWalkableWorldPosition(17 * 16 + 8, 6 * 16 + 8)).toBe(false);
    expect(isWalkableWorldPosition(46 * 16 + 8, 60 * 16 + 8)).toBe(true);
    expect(isWalkableWorldPosition(FARM_PLOTS[0].slots[0].centerX, FARM_PLOTS[0].slots[0].centerY)).toBe(true);
  });

  it("joins the western river to an eight-cell-deep southern water band", () => {
    for (let row = 60; row < 68; row += 1) {
      expect(MUSE_GARDEN_TERRAIN.terrainAt(30, row)).toBe("WATER");
    }
    for (let row = 54; row <= 60; row += 1) {
      expect(MUSE_GARDEN_TERRAIN.terrainAt(10, row)).toBe("WATER");
    }
  });

  it("places the west and south bridges across water with connected road ends", () => {
    expect(MUSE_GARDEN_TERRAIN.terrainAt(3, 30)).toBe("GRASS");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(4, 30)).toBe("WATER");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(8, 30)).toBe("WATER");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(8, 32)).toBe("BRIDGE");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(1, 32)).toBe("PATH");
    for (let row = 35; row <= 37; row += 1) {
      expect(MUSE_GARDEN_TERRAIN.terrainAt(13, row)).toBe("GRASS");
      expect(MUSE_GARDEN_TERRAIN.terrainAt(12, row)).toBe("WATER");
    }
    expect(MUSE_GARDEN_TERRAIN.terrainAt(13, 32)).toBe("PATH");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(14, 32)).toBe("PATH");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(45, 59)).toBe("PATH");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(43, 63)).toBe("WATER");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(47, 63)).toBe("BRIDGE");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(49, 63)).toBe("WATER");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(47, 57)).toBe("PATH");
  });

  it("keeps bridges on water only and the same width as their roads", () => {
    for (let row = 31; row < 35; row += 1) {
      for (let column = 4; column < 13; column += 1) {
        expect(MUSE_GARDEN_TERRAIN.terrainAt(column, row)).toBe("BRIDGE");
      }
      expect(MUSE_GARDEN_TERRAIN.terrainAt(3, row)).toBe("PATH");
      expect(MUSE_GARDEN_TERRAIN.terrainAt(13, row)).toBe("PATH");
    }

    for (let row = 60; row < 68; row += 1) {
      for (let column = 45; column < 49; column += 1) {
        expect(MUSE_GARDEN_TERRAIN.terrainAt(column, row)).toBe("BRIDGE");
      }
      expect(MUSE_GARDEN_TERRAIN.terrainAt(44, row)).toBe("WATER");
      expect(MUSE_GARDEN_TERRAIN.terrainAt(49, row)).toBe("WATER");
    }
  });

  it("keeps every road and bridge cell in one connected network", () => {
    const key = (column: number, row: number) => `${column},${row}`;
    const roadCells = new Set<string>();
    for (const { column, row, terrain } of MUSE_GARDEN_TERRAIN.entries()) {
      if (terrain === "PATH" || terrain === "BRIDGE") roadCells.add(key(column, row));
    }
    const visited = new Set<string>();
    const queue: Array<[number, number]> = [[1, 32]];
    while (queue.length > 0) {
      const [column, row] = queue.shift()!;
      const current = key(column, row);
      if (visited.has(current) || !roadCells.has(current)) continue;
      visited.add(current);
      queue.push([column - 1, row], [column + 1, row], [column, row - 1], [column, row + 1]);
    }
    expect(visited).toEqual(roadCells);
  });

  it("matches every field entrance to the four-cell-wide middle planting column", () => {
    for (const [column, row] of [
      [26, 26], [67, 27],
      [26, 40], [62, 40],
      [26, 50], [62, 50],
    ] as const) {
      for (let offset = 0; offset < 4; offset += 1) {
        expect(MUSE_GARDEN_TERRAIN.terrainAt(column + offset, row)).toBe("PATH");
      }
      expect(MUSE_GARDEN_TERRAIN.terrainAt(column - 1, row)).not.toBe("PATH");
      expect(MUSE_GARDEN_TERRAIN.terrainAt(column + 4, row)).not.toBe("PATH");
    }
  });
});

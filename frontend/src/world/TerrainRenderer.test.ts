import { Texture } from "pixi.js";
import { describe, expect, it } from "vitest";

import { MUSE_GARDEN_TERRAIN, type TerrainMap, type TerrainType } from "./TerrainMap";
import { createTerrainLayer, grassVariantAt, terrainBoundaryEdgesAt, waterBankEdgesAt } from "./TerrainRenderer";
import type { TerrainTextures } from "./TerrainTextures";

const textures: TerrainTextures = { grass: [Texture.WHITE, Texture.WHITE], path: Texture.WHITE, water: Texture.WHITE };

function mapWithCells(cells: Record<string, TerrainType>): TerrainMap {
  return {
    width: 48,
    height: 48,
    cellSize: 16,
    terrainAt(column, row) { return cells[`${column},${row}`] ?? "WATER"; },
    *entries() { for (const [key, terrain] of Object.entries(cells)) { const [column, row] = key.split(",").map(Number); yield { column, row, terrain }; } },
  };
}

describe("Mini Meadow terrain renderer", () => {
  it("chooses grass variation deterministically without changing terrain data", () => {
    expect(grassVariantAt(4, 7)).toBe(grassVariantAt(4, 7));
    expect(MUSE_GARDEN_TERRAIN.terrainAt(4, 7)).toBe("GRASS");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(26, 26)).toBe("PATH");
    expect(MUSE_GARDEN_TERRAIN.terrainAt(21, 17)).toBe("SOIL");
  });

  it("uses the second grass texture often enough to break large-area repetition", () => {
    const variants = [...MUSE_GARDEN_TERRAIN.entries()].filter((entry) => entry.terrain === "GRASS").map(({ column, row }) => grassVariantAt(column, row));
    const variantBCount = variants.filter((variant) => variant === 1).length;
    expect(variantBCount).toBeGreaterThan(variants.length * 0.15);
    expect(variantBCount).toBeLessThan(variants.length * 0.25);
  });

  it("uses exactly one fixed-width bank edge for each WATER-to-land side and none against bridges", () => {
    expect(waterBankEdgesAt(mapWithCells({ "1,1": "WATER", "1,0": "GRASS" }), 1, 1)).toEqual(["N"]);
    expect(waterBankEdgesAt(mapWithCells({ "1,1": "WATER", "1,0": "PATH", "2,1": "SOIL" }), 1, 1)).toEqual(["N", "E"]);
    expect(waterBankEdgesAt(mapWithCells({ "1,1": "WATER", "1,0": "BRIDGE" }), 1, 1)).toEqual([]);
  });

  it("only outlines the exterior of connected bridge and structure cells", () => {
    const bridge = mapWithCells({ "1,1": "BRIDGE", "2,1": "BRIDGE", "1,2": "BRIDGE", "2,2": "BRIDGE" });
    expect(terrainBoundaryEdgesAt(bridge, "BRIDGE", 1, 1)).toEqual(["N", "W"]);
    expect(terrainBoundaryEdgesAt(bridge, "BRIDGE", 2, 2)).toEqual(["S", "E"]);
    expect(terrainBoundaryEdgesAt(bridge, "STRUCTURE", 1, 1)).toEqual([]);
  });

  it("renders grass, water, paths and uniform bank outlines in separate layers", () => {
    const layer = createTerrainLayer(MUSE_GARDEN_TERRAIN, textures);
    const entries = [...MUSE_GARDEN_TERRAIN.entries()];
    const child = (label: string) => layer.children.find((entry) => entry.label === label);
    expect(child("mini-meadow-grass-tiles")?.children).toHaveLength(entries.filter((entry) => entry.terrain === "GRASS").length);
    expect(child("mini-meadow-water-tiles")?.children).toHaveLength(entries.filter((entry) => entry.terrain === "WATER").length);
    expect(child("mini-meadow-path-tiles")?.children).toHaveLength(entries.filter((entry) => entry.terrain === "PATH").length);
    expect(child("pixel-wood-bridge-details")).toBeTruthy();
    expect(child("pixel-structure-details")).toBeTruthy();
    expect(child("uniform-water-bank-outlines")).toBeTruthy();
    expect(child("terrain-transition-details")).toBeTruthy();
    expect(child("garden-landmarks")).toBeTruthy();
    expect(layer.children).toHaveLength(9);
  });
});

import { Container, Graphics, Sprite, type Texture } from "pixi.js";

import { TERRAIN_COLORS, TERRAIN_FEATURE_COLORS } from "./TerrainColors";
import type { TerrainMap, TerrainType } from "./TerrainMap";
import type { TerrainTextures } from "./TerrainTextures";

const WATER_BANK_OUTLINE = 0x1e1c28;
const CARDINAL_DIRECTIONS = [
  { name: "N", offsetX: 0, offsetY: -1 },
  { name: "S", offsetX: 0, offsetY: 1 },
  { name: "E", offsetX: 1, offsetY: 0 },
  { name: "W", offsetX: -1, offsetY: 0 },
] as const;
export type WaterBankDirection = (typeof CARDINAL_DIRECTIONS)[number]["name"];
export type TerrainBoundaryDirection = WaterBankDirection;

interface TerrainRegion {
  readonly cells: readonly { column: number; row: number }[];
  readonly minColumn: number;
  readonly maxColumn: number;
  readonly minRow: number;
  readonly maxRow: number;
  readonly isRectangle: boolean;
}

function coordinateHash(column: number, row: number): number {
  return (Math.imul(column + 17, 1103515245) ^ Math.imul(row + 31, 12345)) >>> 0;
}

/** Stable coordinate hash: variation survives refreshes without storing visual state. */
export function grassVariantAt(column: number, row: number): 0 | 1 {
  return coordinateHash(column, row) % 5 === 0 ? 1 : 0;
}

/**
 * One 1px line is drawn for every WATER-to-land boundary. Bridges are excluded so their deck stays uninterrupted.
 * Keeping the outline procedural avoids variable-width lines from compositing edge sprites at river corners.
 */
export function waterBankEdgesAt(map: TerrainMap, column: number, row: number): readonly WaterBankDirection[] {
  if (map.terrainAt(column, row) !== "WATER") return [];
  return CARDINAL_DIRECTIONS
    .filter(({ offsetX, offsetY }) => {
      const adjacent = map.terrainAt(column + offsetX, row + offsetY);
      return adjacent !== "WATER" && adjacent !== "BRIDGE";
    })
    .map(({ name }) => name);
}

/** Boundary-only outlines keep neighbouring bridge cells visually continuous. */
export function terrainBoundaryEdgesAt(
  map: TerrainMap,
  terrain: "BRIDGE" | "STRUCTURE",
  column: number,
  row: number,
): readonly TerrainBoundaryDirection[] {
  if (map.terrainAt(column, row) !== terrain) return [];
  return CARDINAL_DIRECTIONS
    .filter(({ offsetX, offsetY }) => map.terrainAt(column + offsetX, row + offsetY) !== terrain)
    .map(({ name }) => name);
}

function regionsFor(map: TerrainMap, terrain: TerrainType): readonly TerrainRegion[] {
  const cells = new Set(
    [...map.entries()]
      .filter((entry) => entry.terrain === terrain)
      .map(({ column, row }) => `${column},${row}`),
  );
  const regions: TerrainRegion[] = [];
  while (cells.size > 0) {
    const first = cells.values().next().value as string;
    const queue = [first];
    const regionCells: { column: number; row: number }[] = [];
    cells.delete(first);
    while (queue.length > 0) {
      const key = queue.shift() as string;
      const [column, row] = key.split(",").map(Number);
      regionCells.push({ column, row });
      for (const { offsetX, offsetY } of CARDINAL_DIRECTIONS) {
        const neighbour = `${column + offsetX},${row + offsetY}`;
        if (cells.delete(neighbour)) queue.push(neighbour);
      }
    }
    const columns = regionCells.map((cell) => cell.column);
    const rows = regionCells.map((cell) => cell.row);
    const minColumn = Math.min(...columns);
    const maxColumn = Math.max(...columns);
    const minRow = Math.min(...rows);
    const maxRow = Math.max(...rows);
    const isRectangle = regionCells.length === (maxColumn - minColumn + 1) * (maxRow - minRow + 1);
    regions.push({ cells: regionCells, minColumn, maxColumn, minRow, maxRow, isRectangle });
  }
  return regions;
}

function addTerrainSprite(layer: Container, texture: Texture, x: number, y: number, width: number, height: number): void {
  const tile = new Sprite(texture);
  tile.position.set(x, y);
  tile.width = width;
  tile.height = height;
  layer.addChild(tile);
}

function drawWaterBankEdge(graphics: Graphics, direction: WaterBankDirection, x: number, y: number, width: number, height: number): void {
  if (direction === "N") graphics.moveTo(x, y).lineTo(x + width, y).stroke({ color: WATER_BANK_OUTLINE, width: 1 });
  if (direction === "S") graphics.moveTo(x, y + height).lineTo(x + width, y + height).stroke({ color: WATER_BANK_OUTLINE, width: 1 });
  if (direction === "E") graphics.moveTo(x + width, y).lineTo(x + width, y + height).stroke({ color: WATER_BANK_OUTLINE, width: 1 });
  if (direction === "W") graphics.moveTo(x, y).lineTo(x, y + height).stroke({ color: WATER_BANK_OUTLINE, width: 1 });
}

function drawBoundary(graphics: Graphics, direction: TerrainBoundaryDirection, x: number, y: number, size: number, color: string): void {
  if (direction === "N") graphics.moveTo(x, y).lineTo(x + size, y).stroke({ color, width: 1 });
  if (direction === "S") graphics.moveTo(x, y + size).lineTo(x + size, y + size).stroke({ color, width: 1 });
  if (direction === "E") graphics.moveTo(x + size, y).lineTo(x + size, y + size).stroke({ color, width: 1 });
  if (direction === "W") graphics.moveTo(x, y).lineTo(x, y + size).stroke({ color, width: 1 });
}

function terrainEdgesAt(map: TerrainMap, terrain: TerrainType, column: number, row: number): readonly TerrainBoundaryDirection[] {
  return CARDINAL_DIRECTIONS
    .filter(({ offsetX, offsetY }) => map.terrainAt(column + offsetX, row + offsetY) !== terrain)
    .map(({ name }) => name);
}

function drawTerrainTransitions(graphics: Graphics, map: TerrainMap): void {
  const size = map.cellSize;
  for (const { column, row, terrain } of map.entries()) {
    const x = column * size;
    const y = row * size;
    if (terrain === "PATH") {
      for (const direction of terrainEdgesAt(map, "PATH", column, row)) {
        drawBoundary(graphics, direction, x, y, size, "#8d663f");
        if (direction === "N") graphics.moveTo(x + 2, y + 2).lineTo(x + size - 2, y + 2).stroke({ color: "#e1c585", alpha: .58, width: 1 });
        if (direction === "W") graphics.moveTo(x + 2, y + 2).lineTo(x + 2, y + size - 2).stroke({ color: "#e1c585", alpha: .42, width: 1 });
      }
      // The road's pebbles follow its grid rhythm rather than appearing in unrelated terrain.
      if ((column * 3 + row) % 5 === 0) {
        graphics.circle(x + size * .36, y + size * .62, 1).fill({ color: "#ead08c", alpha: .7 });
        graphics.circle(x + size * .7, y + size * .35, .8).fill({ color: "#8f6844", alpha: .6 });
      }
    }
    if (terrain === "SOIL") {
      for (const direction of terrainEdgesAt(map, "SOIL", column, row)) {
        drawBoundary(graphics, direction, x, y, size, "#4d3027");
        if (direction === "N") graphics.moveTo(x + 1, y + 2).lineTo(x + size - 1, y + 2).stroke({ color: "#a56e4e", alpha: .65, width: 1 });
      }
    }
  }
}

function drawGardenLandmarks(graphics: Graphics): void {
  // Low flower beds are walkable scenery; the real tree groves use TREE terrain.
  [[18, 29], [32, 24], [39, 20], [54, 21], [72, 33], [33, 48], [53, 55], [70, 39]].forEach(([column, row]) => {
    const x = column * 16;
    const y = row * 16;
    graphics.circle(x + 8, y + 8, 5).fill("#3f7543");
    graphics.circle(x + 5, y + 6, 2).fill("#edc870");
    graphics.circle(x + 10, y + 5, 2).fill("#e59bb0");
    graphics.circle(x + 11, y + 10, 2).fill("#d8e18a");
  });
}

function drawTreeRegion(graphics: Graphics, map: TerrainMap, region: TerrainRegion): void {
  const size = map.cellSize;
  const left = region.minColumn * size;
  const top = region.minRow * size;
  const width = (region.maxColumn - region.minColumn + 1) * size;
  const height = (region.maxRow - region.minRow + 1) * size;
  const centreX = left + width / 2;
  const canopyY = top + height * .45;
  const radius = Math.min(width, height);
  graphics.ellipse(centreX, top + height - 4, width * .57, height * .18).fill({ color: "#142d1e", alpha: .55 });
  graphics.rect(centreX - 4, canopyY, 8, height * .52).fill("#67442f");
  graphics.rect(centreX - 2, canopyY, 2, height * .5).fill("#b2794b");
  for (const [offsetX, offsetY, scale] of [[-.34, .24, .34], [0, .12, .42], [.32, .27, .33], [-.18, -.08, .34], [.2, -.08, .34]] as const) {
    graphics.circle(centreX + width * offsetX, canopyY + height * offsetY, radius * scale).fill("#285b37");
    graphics.circle(centreX + width * (offsetX - .04), canopyY + height * (offsetY - .04), radius * scale * .72).fill("#3d7b45");
  }
  graphics.circle(centreX - width * .18, canopyY - height * .05, radius * .12).fill({ color: "#83ae5c", alpha: .72 });
}

function drawBridgeRegion(graphics: Graphics, map: TerrainMap, region: TerrainRegion): void {
  const size = map.cellSize;
  for (const { column, row } of region.cells) {
    const x = column * size;
    const y = row * size;
    graphics.rect(x, y, size, size).fill(TERRAIN_FEATURE_COLORS.bridgeDeck);
    for (const edge of terrainBoundaryEdgesAt(map, "BRIDGE", column, row)) {
      drawBoundary(graphics, edge, x, y, size, TERRAIN_FEATURE_COLORS.bridgeOutline);
    }
  }
  const horizontal = region.maxColumn - region.minColumn >= region.maxRow - region.minRow;
  if (!region.isRectangle) return;
  const left = region.minColumn * size;
  const top = region.minRow * size;
  const width = (region.maxColumn - region.minColumn + 1) * size;
  const height = (region.maxRow - region.minRow + 1) * size;
  if (horizontal) {
    for (let x = left + 6; x < left + width; x += 6) {
      graphics.moveTo(x, top + 1).lineTo(x, top + height - 1).stroke({ color: TERRAIN_FEATURE_COLORS.bridgePlank, width: 1 });
    }
    graphics.moveTo(left + 1, top + 2).lineTo(left + width - 1, top + 2).stroke({ color: TERRAIN_FEATURE_COLORS.bridgeHighlight, width: 1 });
    for (let x = left + 5; x < left + width; x += 24) {
      graphics.rect(x, top + 1, 2, 3).fill("#5b3727");
      graphics.rect(x, top + height - 4, 2, 3).fill("#5b3727");
    }
  } else {
    for (let y = top + 6; y < top + height; y += 6) {
      graphics.moveTo(left + 1, y).lineTo(left + width - 1, y).stroke({ color: TERRAIN_FEATURE_COLORS.bridgePlank, width: 1 });
    }
    graphics.moveTo(left + 2, top + 1).lineTo(left + 2, top + height - 1).stroke({ color: TERRAIN_FEATURE_COLORS.bridgeHighlight, width: 1 });
    for (let y = top + 5; y < top + height; y += 24) {
      graphics.rect(left + 1, y, 3, 2).fill("#5b3727");
      graphics.rect(left + width - 4, y, 3, 2).fill("#5b3727");
    }
  }
}

function drawStructureRegion(graphics: Graphics, map: TerrainMap, region: TerrainRegion): void {
  const size = map.cellSize;
  for (const { column, row } of region.cells) {
    const x = column * size;
    const y = row * size;
    graphics.rect(x, y, size, size).fill(TERRAIN_FEATURE_COLORS.structureRoof);
    for (const edge of terrainBoundaryEdgesAt(map, "STRUCTURE", column, row)) {
      drawBoundary(graphics, edge, x, y, size, TERRAIN_FEATURE_COLORS.structureOutline);
    }
  }
  if (!region.isRectangle) return;
  const left = region.minColumn * size;
  const top = region.minRow * size;
  const width = (region.maxColumn - region.minColumn + 1) * size;
  const height = (region.maxRow - region.minRow + 1) * size;
  graphics.rect(left + 2, top + 2, width - 4, Math.max(2, Math.floor(height / 3))).fill(TERRAIN_FEATURE_COLORS.structureRoofLight);
  for (let y = top + 8; y < top + height - 3; y += 8) {
    graphics.moveTo(left + 2, y).lineTo(left + width - 2, y).stroke({ color: TERRAIN_FEATURE_COLORS.structureRoofShade, width: 1 });
  }
  const entranceX = left + Math.floor(width / 2) - 3;
  graphics.rect(entranceX, top + height - 3, 6, 3).fill(TERRAIN_FEATURE_COLORS.structureEntry);
}

/**
 * Small deterministic details stop the large terrain fields from reading as a
 * flat tile sheet. They live in the existing primitive layer so they remain
 * crisp and do not add another texture or runtime dependency.
 */
function drawGardenDetails(graphics: Graphics, map: TerrainMap): void {
  const size = map.cellSize;
  for (const { column, row, terrain } of map.entries()) {
    const hash = coordinateHash(column, row);
    const x = column * size;
    const y = row * size;
    if (terrain === "GRASS") {
      if (hash % 7 === 0) {
        graphics
          .moveTo(x + size * .34, y + size * .73).lineTo(x + size * .44, y + size * .43)
          .moveTo(x + size * .48, y + size * .73).lineTo(x + size * .59, y + size * .36)
          .moveTo(x + size * .62, y + size * .73).lineTo(x + size * .69, y + size * .49)
          .stroke({ color: "#376f43", width: 1 });
      }
      if (hash % 19 === 0) {
        graphics.circle(x + size * .5, y + size * .48, 1.2).fill("#f5d96c");
        graphics.circle(x + size * .38, y + size * .52, .9).fill("#f1c7cc");
        graphics.circle(x + size * .62, y + size * .52, .9).fill("#f1c7cc");
      }
      if (hash % 29 === 0) {
        graphics.ellipse(x + size * .52, y + size * .67, 2.5, 1.5).fill("#829270");
      }
    }
    if (terrain === "WATER" && hash % 7 === 0) {
      graphics
        .moveTo(x + size * .25, y + size * .45).lineTo(x + size * .66, y + size * .45)
        .moveTo(x + size * .4, y + size * .64).lineTo(x + size * .76, y + size * .64)
        .stroke({ color: "#9bc4d5", alpha: .5, width: 1 });
    }
    if (terrain === "WATER" && hash % 29 === 0) {
      graphics.ellipse(x + size * .58, y + size * .56, 3.5, 1.8).fill("#6e9c62");
      graphics.circle(x + size * .6, y + size * .43, 1.2).fill("#e8bbd0");
    }
    if (terrain === "WATER" && hash % 13 === 0 && waterBankEdgesAt(map, column, row).length > 0) {
      graphics
        .moveTo(x + size * .28, y + size * .82).lineTo(x + size * .35, y + size * .34)
        .moveTo(x + size * .43, y + size * .82).lineTo(x + size * .5, y + size * .42)
        .stroke({ color: "#416c40", width: 1.2 });
    }
    if (terrain === "SOIL") {
      for (let offset = 4; offset < size; offset += 5) {
        graphics.moveTo(x + 2, y + offset).lineTo(x + size - 2, y + offset - 1).stroke({ color: "#5e4031", alpha: .55, width: 1 });
      }
    }
  }
}

/** Draws GRASS, PATH and WATER as Mini Meadow textures; other terrain remains a Pixi primitive. */
export function createTerrainLayer(map: TerrainMap, textures: TerrainTextures): Container {
  const layer = new Container();
  const graphics = new Graphics();
  const grass = new Container();
  const water = new Container();
  const paths = new Container();
  const waterBanks = new Graphics();
  const transitions = new Graphics();
  const bridges = new Graphics();
  const structures = new Graphics();
  const trees = new Graphics();
  const landmarks = new Graphics();
  layer.label = "grid-terrain-map";
  grass.label = "mini-meadow-grass-tiles";
  water.label = "mini-meadow-water-tiles";
  paths.label = "mini-meadow-path-tiles";
  waterBanks.label = "uniform-water-bank-outlines";
  transitions.label = "terrain-transition-details";
  bridges.label = "pixel-wood-bridge-details";
  structures.label = "pixel-structure-details";
  trees.label = "tree-grove-obstacles";
  landmarks.label = "garden-landmarks";

  for (const { column, row, terrain } of map.entries()) {
    const x = column * map.cellSize;
    const y = row * map.cellSize;
    const width = Math.min(map.cellSize, map.width - x);
    const height = Math.min(map.cellSize, map.height - y);
    if (terrain === "GRASS" || terrain === "TREE") {
      addTerrainSprite(grass, textures.grass[grassVariantAt(column, row)], x, y, width, height);
    } else if (terrain === "WATER") {
      addTerrainSprite(water, textures.water, x, y, width, height);
      for (const direction of waterBankEdgesAt(map, column, row)) {
        drawWaterBankEdge(waterBanks, direction, x, y, width, height);
      }
    } else if (terrain === "PATH") {
      addTerrainSprite(paths, textures.path, x, y, width, height);
    } else {
      graphics.rect(x, y, width, height).fill(TERRAIN_COLORS[terrain]);
    }
  }
  drawGardenDetails(graphics, map);
  drawTerrainTransitions(transitions, map);
  for (const region of regionsFor(map, "BRIDGE")) drawBridgeRegion(bridges, map, region);
  for (const region of regionsFor(map, "STRUCTURE")) drawStructureRegion(structures, map, region);
  for (const region of regionsFor(map, "TREE")) drawTreeRegion(trees, map, region);
  drawGardenLandmarks(landmarks);
  // Banks are above land textures for a consistently visible edge; bridges have no bank edge and remain uninterrupted.
  layer.addChild(grass, water, graphics, paths, transitions, bridges, structures, waterBanks, trees, landmarks);
  return layer;
}


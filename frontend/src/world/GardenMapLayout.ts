import type { GardenRenderSpec } from "../rendering/flowers/types";
import {
  FARM_PLOTS,
  TERRAIN_CELL_SIZE,
  type FarmSlot,
} from "./TerrainMap";

export interface GardenSlotBinding {
  readonly gridX: number;
  readonly gridY: number;
  readonly slot: FarmSlot;
}

/**
 * Stable frontend bindings for the 24 V1 planting positions. The backend keeps
 * receiving its existing grid_x / grid_y IDs; only their world presentation is
 * mapped onto the four visible fields.
 */
export const GARDEN_SLOT_BINDINGS: readonly GardenSlotBinding[] = FARM_PLOTS.flatMap((plot, plotIndex) =>
  plot.slots.map((slot, slotIndex) => ({
    gridX: 7 + (plotIndex % 2) * 3 + (slotIndex % 3),
    gridY: 4 + Math.floor(plotIndex / 2) * 2 + Math.floor(slotIndex / 3),
    slot,
  })),
);

const BINDING_BY_BACKEND_GRID = new Map(
  GARDEN_SLOT_BINDINGS.map((binding) => [`${binding.gridX},${binding.gridY}`, binding] as const),
);

export function gardenSlotBinding(gridX: number, gridY: number): GardenSlotBinding | undefined {
  return BINDING_BY_BACKEND_GRID.get(`${gridX},${gridY}`);
}

export function gardenWorldPosition(
  gridX: number,
  gridY: number,
  fallback: { x: number; y: number },
): { x: number; y: number } {
  const binding = gardenSlotBinding(gridX, gridY);
  return binding ? { x: binding.slot.centerX, y: binding.slot.centerY } : fallback;
}

export function legacyTerrainTile(gridX: number, gridY: number): { x: number; y: number } | undefined {
  const binding = gardenSlotBinding(gridX, gridY);
  if (!binding) return undefined;
  return {
    x: Math.floor(binding.slot.centerX / TERRAIN_CELL_SIZE),
    y: Math.floor(binding.slot.centerY / TERRAIN_CELL_SIZE),
  };
}

export function flowerOccupiedTiles(flower: GardenRenderSpec["flowers"][number]): [number, number][] {
  if (flower.placement_schema_version === "terrain-v1" && flower.occupied_tiles?.length) {
    return flower.occupied_tiles;
  }
  const legacy = legacyTerrainTile(flower.grid_x, flower.grid_y);
  return legacy ? [[legacy.x, legacy.y]] : [];
}

export function flowerWorldPosition(
  flower: GardenRenderSpec["flowers"][number],
): { x: number; y: number } {
  if (flower.placement_schema_version === "terrain-v1") {
    return {
      x: (flower.grid_x + 0.5) * TERRAIN_CELL_SIZE,
      y: (flower.grid_y + 0.5) * TERRAIN_CELL_SIZE,
    };
  }
  return gardenWorldPosition(
    flower.grid_x,
    flower.grid_y,
    { x: flower.pixel_x, y: flower.pixel_y },
  );
}

/** Relocates mapped flowers for rendering while preserving IDs and backend coordinates. */
export function mapGardenSpecToWorld(spec: GardenRenderSpec): GardenRenderSpec {
  return {
    ...spec,
    flowers: spec.flowers.map((flower) => {
      const world = flowerWorldPosition(flower);
      return { ...flower, pixel_x: world.x, pixel_y: world.y };
    }),
  };
}

export const GARDEN_SLOT_INTERACTION_SIZE = TERRAIN_CELL_SIZE * 4;

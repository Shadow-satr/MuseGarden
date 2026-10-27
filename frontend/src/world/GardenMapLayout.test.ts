import { describe, expect, it } from "vitest";

import type { GardenRenderSpec } from "../rendering/flowers/types";
import {
  GARDEN_SLOT_BINDINGS,
  flowerOccupiedTiles,
  flowerWorldPosition,
  gardenSlotBinding,
  gardenWorldPosition,
  mapGardenSpecToWorld,
} from "./GardenMapLayout";

describe("Garden map layout bindings", () => {
  it("binds exactly six backend cells to each of four visible fields", () => {
    expect(GARDEN_SLOT_BINDINGS).toHaveLength(24);
    const counts = new Map<string, number>();
    for (const binding of GARDEN_SLOT_BINDINGS) {
      counts.set(binding.slot.plotId, (counts.get(binding.slot.plotId) ?? 0) + 1);
    }
    expect([...counts.values()]).toEqual([6, 6, 6, 6]);
    expect(gardenSlotBinding(8, 5)?.slot).toMatchObject({ plotId: "north-west", slot: 4 });
  });

  it("maps bound flowers to farm slots and preserves legacy flower positions", () => {
    expect(gardenWorldPosition(8, 5, { x: 1, y: 2 })).toEqual({ x: 448, y: 384 });
    expect(gardenWorldPosition(14, 9, { x: 700, y: 456 })).toEqual({ x: 700, y: 456 });

    const spec = {
      cell_size: 48,
      flowers: [
        { grid_x: 8, grid_y: 5, pixel_x: 408, pixel_y: 264 },
        { grid_x: 14, grid_y: 9, pixel_x: 696, pixel_y: 456 },
      ],
    } as GardenRenderSpec;
    const mapped = mapGardenSpecToWorld(spec);
    expect(mapped.cell_size).toBe(spec.cell_size);
    expect(mapped.flowers[0]).toMatchObject({ grid_x: 8, grid_y: 5, pixel_x: 448, pixel_y: 384 });
    expect(mapped.flowers[1]).toMatchObject({ grid_x: 14, grid_y: 9, pixel_x: 696, pixel_y: 456 });
    expect(spec.flowers[0]).toMatchObject({ pixel_x: 408, pixel_y: 264 });
  });

  it("uses persisted terrain centers and footprints for Step 14 flowers", () => {
    const flower = {
      grid_x: 22,
      grid_y: 18,
      pixel_x: 0,
      pixel_y: 0,
      placement_schema_version: "terrain-v1",
      flower_size: "large",
      occupied_tiles: [[21, 17], [22, 17], [23, 17], [21, 18], [22, 18], [23, 18], [21, 19], [22, 19], [23, 19]],
    } as GardenRenderSpec["flowers"][number];
    expect(flowerWorldPosition(flower)).toEqual({ x: 360, y: 296 });
    expect(flowerOccupiedTiles(flower)).toHaveLength(9);
    expect(flowerOccupiedTiles(flower)).toContainEqual([22, 18]);
  });
});

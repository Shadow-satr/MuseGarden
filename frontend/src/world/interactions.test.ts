import { describe, expect, it, vi } from "vitest";

import type { GardenRenderSpec } from "../rendering/flowers/types";
import { createInteractables, InteractionManager, type Interactable } from "./interactions";

const empty: Interactable = { kind: "plant-spot", id: "spot", x: 10, y: 10, gridX: 0, gridY: 0, cellSize: 20, prompt: "种下记忆" };
const flower: Interactable = { kind: "flower", id: "flower", x: 50, y: 10, gridX: 2, gridY: 0, cellSize: 20, plantingRecordId: "planting", flowerArtifactId: "artifact", prompt: "查看记忆" };

describe("Interaction System", () => {
  it("finds a nearby spot, clears it on departure, and ignores E without a target", () => {
    const onInteract = vi.fn();
    const manager = new InteractionManager([empty], onInteract);
    expect(manager.update(14, 10)).toBe(empty);
    manager.interact();
    expect(onInteract).toHaveBeenCalledWith(empty);
    expect(manager.update(100, 100)).toBeNull();
    manager.interact();
    expect(onInteract).toHaveBeenCalledTimes(1);
  });

  it("identifies a flower only after the player's feet enter its cell", () => {
    const manager = new InteractionManager([empty, flower], vi.fn());
    expect(manager.update(39, 10)).toBeNull();
    expect(manager.update(40, 10)).toBe(flower);
    expect(manager.currentTarget?.prompt).toBe("查看记忆");
    expect(manager.update(12, 10)).toBe(empty);
    expect(manager.update(50, 20)).toBeNull();
  });

  it("activates a planting spot only when the player's feet enter its cell", () => {
    const spot: Interactable = {
      kind: "plant-spot", id: "spot:2,2", x: 120, y: 120,
      gridX: 2, gridY: 2, cellSize: 48, prompt: "种下记忆",
    };
    const manager = new InteractionManager([spot], vi.fn());
    expect(manager.update(95, 120)).toBeNull();
    expect(manager.update(96, 120)).toBe(spot); // Top/left edge belongs to this cell.
    expect(manager.update(143, 143)).toBe(spot);
    expect(manager.update(144, 120)).toBeNull();
  });

  it("chooses the nearest target if multiple objects share one cell", () => {
    const near = { ...flower, id: "near", x: 42 };
    const manager = new InteractionManager([flower, near], vi.fn());
    expect(manager.update(41, 10)).toBe(near);
  });

  it("exposes every unoccupied SOIL terrain tile as a planting position", () => {
    const spec = {
      grid_width: 16, grid_height: 10, cell_size: 48,
      flowers: [{ grid_x: 8, grid_y: 5, pixel_x: 408, pixel_y: 264, planting_record_id: "planted", flower_artifact_id: "artifact" }],
    } as GardenRenderSpec;
    const targets = createInteractables(spec);
    expect(targets.filter((target) => target.kind === "plant-spot")).toHaveLength(443);
    expect(targets.find((target) => target.id === "flower:planted")?.prompt).toBe("查看记忆");
    expect(targets.find((target) => target.id === "flower:planted")).toMatchObject({
      plantingRecordId: "planted", flowerArtifactId: "artifact", x: 448, y: 384,
    });
    expect(targets.some((target) => target.id === "spot:28,24")).toBe(false);
    expect(targets.some((target) => target.id === "spot:21,17")).toBe(true);
    expect(targets.some((target) => target.id === "spot:70,49")).toBe(true);
    expect(targets.some((target) => target.id === "spot:0,0")).toBe(false);
  });

  it("maps all nine occupied tiles of a large flower to one memory target", () => {
    const spec = {
      grid_width: 91, grid_height: 68, cell_size: 48,
      flowers: [{
        grid_x: 22, grid_y: 18, pixel_x: 0, pixel_y: 0,
        planting_record_id: "large", flower_artifact_id: "artifact-large",
        placement_schema_version: "terrain-v1", flower_size: "large",
        occupied_tiles: [
          [21, 17], [22, 17], [23, 17],
          [21, 18], [22, 18], [23, 18],
          [21, 19], [22, 19], [23, 19],
        ],
      }],
    } as GardenRenderSpec;
    const targets = createInteractables(spec);
    const large = targets.find((target) => target.id === "flower:large")!;
    const manager = new InteractionManager(targets, vi.fn());
    expect(targets.filter((target) => target.kind === "plant-spot")).toHaveLength(435);
    for (const [x, y] of [[21, 17], [23, 17], [21, 19], [23, 19]]) {
      expect(manager.update((x + 0.5) * 16, (y + 0.5) * 16)).toBe(large);
    }
  });
});

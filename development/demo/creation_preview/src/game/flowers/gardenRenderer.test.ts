import { describe, expect, it } from "vitest";

import gardenPreview from "../../../public/garden-preview-spec.json";
import { createGardenScene } from "./gardenRenderer";
import { assertGardenRenderSpec } from "./validate";

describe("Garden renderer contract", () => {
  it("accepts the Python-exported scene and rejects broken dimensions", () => {
    expect(() => assertGardenRenderSpec(gardenPreview)).not.toThrow();
    expect(() => assertGardenRenderSpec({ ...gardenPreview, pixel_width: 999 })).toThrow();
    expect(() => assertGardenRenderSpec({
      ...gardenPreview,
      flowers: [...gardenPreview.flowers].reverse(),
    })).toThrow();
  });

  it("builds one depth-sorted Pixi placement for every flower", () => {
    assertGardenRenderSpec(gardenPreview);
    const scene = createGardenScene(gardenPreview);

    expect(scene.container.label).toBe(`garden:${gardenPreview.garden_id}`);
    expect(scene.container.children).toHaveLength(gardenPreview.flowers.length + 1);
    for (const placement of gardenPreview.flowers) {
      const child = scene.container.children.find(
        (entry) => entry.label === `planting:${placement.planting_record_id}`,
      );
      expect(child).toBeTruthy();
      expect(child!.x).toBe(placement.pixel_x);
      expect(child!.y).toBe(placement.pixel_y);
      expect(child!.scale.x).toBe(placement.scale);
      expect(child!.zIndex).toBe(placement.z_index);
    }

    expect(() => scene.update(1200)).not.toThrow();
    scene.setHighlight({ x: 3, y: 3 });
    expect(scene.container.children.find((entry) => entry.label === "highlight:3,3")).toBeTruthy();
    scene.setHighlight({ x: 4, y: 2 });
    expect(scene.container.children.find((entry) => entry.label === "highlight:3,3")).toBeFalsy();
    expect(scene.container.children.find((entry) => entry.label === "highlight:4,2")).toBeTruthy();
    scene.setHighlight(null);
    expect(scene.container.children.find((entry) => entry.label?.startsWith("highlight:"))).toBeFalsy();
    scene.destroy();
  });

  it("keeps all templates, sizes and logical positions from the fixture", () => {
    assertGardenRenderSpec(gardenPreview);
    expect(new Set(gardenPreview.flowers.map((flower) => flower.template_id)).size).toBe(9);
    expect(new Set(gardenPreview.flowers.map((flower) => flower.scale)).size).toBeGreaterThan(3);
    expect(new Set(gardenPreview.flowers.map((flower) => `${flower.grid_x}:${flower.grid_y}`)).size).toBe(9);
    expect(gardenPreview.flowers.map((flower) => flower.z_index)).toEqual(
      [...gardenPreview.flowers.map((flower) => flower.z_index)].sort((a, b) => a - b),
    );
  });
});

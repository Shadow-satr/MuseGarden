import { describe, expect, it } from "vitest";
import { Container } from "pixi.js";

import gardenPreview from "../../../../development/fixtures/garden-preview-spec.json";
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
      expect(child!.zIndex).toBe(placement.z_index);
    }

    expect(() => scene.update(1200)).not.toThrow();
    scene.destroy();
  });

  it("renders persisted large flowers at a visibly larger stable scale", () => {
    assertGardenRenderSpec(gardenPreview);
    const source = gardenPreview.flowers[0];
    const occupied = [-1, 0, 1].flatMap((dy) =>
      [-1, 0, 1].map((dx) => [source.grid_x + dx, source.grid_y + dy] as [number, number]),
    );
    const large = {
      ...source,
      planting_record_id: "large-planting",
      flower_size: "large" as const,
      placement_schema_version: "terrain-v1" as const,
      occupied_tiles: occupied,
    };
    const scene = createGardenScene({ ...gardenPreview, flowers: [large] }, { tileSize: 16 });
    const smallScene = createGardenScene({ ...gardenPreview, flowers: [source] }, { tileSize: 16 });
    expect(scene.container.children[1].scale.x).toBeCloseTo(smallScene.container.children[1].scale.x * 3);
    smallScene.destroy();
    scene.destroy();
  });

  it("centers the painted body of every species inside its terrain tile", () => {
    const scene = createGardenScene(gardenPreview, { includeBackground: false, tileSize: 16 });
    for (const anchor of scene.container.children) {
      const flower = (anchor as Container).children[0] as Container;
      for (const layer of flower.children) {
        if (["glow", "particles", "decoration"].includes(layer.label)) layer.visible = false;
      }
      const bounds = anchor.getBounds();
      expect(Math.max(bounds.width, bounds.height)).toBeGreaterThanOrEqual(16 * 0.90 - 0.001);
      expect(bounds.minX).toBeGreaterThan(anchor.x - 8);
      expect(bounds.maxX).toBeLessThan(anchor.x + 8);
      expect(bounds.minY).toBeGreaterThan(anchor.y - 8);
      expect(bounds.maxY).toBeLessThan(anchor.y + 8);
    }
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

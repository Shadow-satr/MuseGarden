import { Container, Graphics } from "pixi.js";

import { createPixelFlower, type PixelFlower } from "./renderer";
import type { GardenRenderSpec } from "./types";
import { assertGardenRenderSpec } from "./validate";

export interface PixelGarden {
  container: Container;
  update(elapsedMs: number): void;
  destroy(): void;
}

function createBackground(spec: GardenRenderSpec) {
  const background = new Graphics()
    .rect(0, 0, spec.pixel_width, spec.pixel_height)
    .fill(spec.background.base_color);

  for (let y = 0; y < spec.grid_height; y += 1) {
    for (let x = 0; x < spec.grid_width; x += 1) {
      if ((x + y) % 2 === 0) {
        background
          .rect(x * spec.cell_size, y * spec.cell_size, spec.cell_size, spec.cell_size)
          .fill({ color: spec.background.tile_color, alpha: 0.2 });
      }
      const marker = (x * 17 + y * 29) % 7;
      if (marker === 0) {
        background
          .rect(x * spec.cell_size + 9, y * spec.cell_size + 14, 3, 2)
          .fill({ color: spec.background.accent_color, alpha: 0.5 });
      }
    }
  }
  return background;
}

export function createGardenScene(input: unknown): PixelGarden {
  assertGardenRenderSpec(input);
  const spec = input;
  const root = new Container();
  root.label = `garden:${spec.garden_id}`;
  root.sortableChildren = true;

  const background = createBackground(spec);
  background.zIndex = -1;
  root.addChild(background);

  const flowers: PixelFlower[] = [];
  for (const placement of spec.flowers) {
    const flower = createPixelFlower(placement.render_spec);
    const anchor = new Container();
    anchor.label = `planting:${placement.planting_record_id}`;
    anchor.position.set(placement.pixel_x, placement.pixel_y);
    anchor.scale.set(placement.scale);
    anchor.zIndex = placement.z_index;
    flower.container.position.set(-24, -59);
    anchor.addChild(flower.container);
    root.addChild(anchor);
    flowers.push(flower);
  }

  return {
    container: root,
    update: (elapsedMs: number) => {
      flowers.forEach((flower) => flower.update(elapsedMs));
    },
    destroy: () => root.destroy({ children: true }),
  };
}

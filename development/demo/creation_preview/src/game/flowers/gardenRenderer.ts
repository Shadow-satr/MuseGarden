import { Container, Graphics } from "pixi.js";

import { createPixelFlower, type PixelFlower } from "./renderer";
import type { GardenRenderSpec } from "./types";
import { assertGardenRenderSpec } from "./validate";

export interface PixelGarden {
  container: Container;
  update(elapsedMs: number): void;
  setGhost(placement: GardenGhostPlacement | null): void;
  setHighlight(cell: { x: number; y: number } | null): void;
  destroy(): void;
}

export interface GardenGhostPlacement {
  renderSpec: GardenRenderSpec["flowers"][number]["render_spec"];
  pixelX: number;
  pixelY: number;
  scale: number;
  zIndex: number;
  valid: boolean;
  cellSize: number;
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
  let ghostAnchor: Container | undefined;
  let ghostFlower: PixelFlower | undefined;
  let highlight: Graphics | undefined;
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

  const setGhost = (placement: GardenGhostPlacement | null) => {
    if (ghostAnchor) {
      root.removeChild(ghostAnchor);
      ghostAnchor.destroy({ children: true });
      ghostAnchor = undefined;
      ghostFlower = undefined;
    }
    if (placement === null) return;

    ghostAnchor = new Container();
    ghostAnchor.label = "planting-ghost";
    ghostAnchor.position.set(placement.pixelX, placement.pixelY);
    ghostAnchor.zIndex = placement.zIndex + 0.5;

    const cell = new Graphics()
      .rect(
        -placement.cellSize / 2,
        -placement.cellSize,
        placement.cellSize,
        placement.cellSize,
      )
      .fill({ color: placement.valid ? "#B9DC83" : "#E66B66", alpha: 0.2 })
      .stroke({ color: placement.valid ? "#D9F2AA" : "#FF9B91", width: 2, alpha: 0.9 });
    ghostAnchor.addChild(cell);

    ghostFlower = createPixelFlower(placement.renderSpec);
    ghostFlower.container.position.set(-24 * placement.scale, -59 * placement.scale);
    ghostFlower.container.scale.set(placement.scale);
    ghostFlower.container.alpha = 0.62;
    ghostAnchor.addChild(ghostFlower.container);
    root.addChild(ghostAnchor);
  };

  const setHighlight = (cell: { x: number; y: number } | null) => {
    if (highlight) {
      root.removeChild(highlight);
      highlight.destroy();
      highlight = undefined;
    }
    if (!cell) return;
    highlight = new Graphics()
      .rect(cell.x * spec.cell_size + 2, cell.y * spec.cell_size + 2,
        spec.cell_size - 4, spec.cell_size - 4)
      .fill({ color: "#F1E78B", alpha: 0.2 })
      .stroke({ color: "#FFF5AD", width: 3, alpha: 0.95 });
    highlight.label = `highlight:${cell.x},${cell.y}`;
    highlight.zIndex = spec.grid_width * spec.grid_height + 1;
    root.addChild(highlight);
  };

  return {
    container: root,
    update: (elapsedMs: number) => {
      flowers.forEach((flower) => flower.update(elapsedMs));
      ghostFlower?.update(elapsedMs);
    },
    setGhost,
    setHighlight,
    destroy: () => root.destroy({ children: true }),
  };
}

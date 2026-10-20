import { Container, Graphics, Sprite, Texture } from "pixi.js";

import { createGardenScene, type PixelGarden } from "../rendering/flowers/gardenRenderer";
import type { GardenRenderSpec } from "../rendering/flowers/types";
import { cameraPositionFor } from "./Camera";
import { MAP_ART_SIZE } from "./MapArt";

const CELL_STABILITY_MS = 45;
const CELL_CROSSFADE_MS = 125;
const CELL_DASH_LENGTH = 6;
const CELL_DASH_GAP = 5;
export const WORLD_EDGE_PADDING = 36;
// At native scale a whole island is visible at once. This shows one field and
// its immediate paths at a time, matching the chosen field-view reference.
export const MAP_VIEW_ZOOM = 2.5;

export function gardenViewportSize(spec: GardenRenderSpec): { width: number; height: number } {
  return {
    width: spec.pixel_width + WORLD_EDGE_PADDING * 2,
    height: spec.pixel_height + WORLD_EDGE_PADDING * 2,
  };
}

/** The formal map has its own art dimensions; gameplay coordinates are map pixels. */
export function mapWorldContentSize(): { width: number; height: number } {
  return MAP_ART_SIZE;
}

function createMapArt(texture: Texture): Sprite {
  const map = new Sprite(texture);
  map.label = "musegarden-map-art";
  map.width = MAP_ART_SIZE.width;
  map.height = MAP_ART_SIZE.height;
  return map;
}

/** Owns Pixi display layers; future world entities belong in entities. */
export class WorldScene {
  readonly container = new Container();
  readonly entities = new Container();
  private readonly world = new Container();
  private garden: PixelGarden;
  private readonly outgoingCellHighlight = new Graphics();
  private readonly cellHighlight = new Graphics();
  private readonly cellSize: number;
  private highlightedGridX = -1;
  private highlightedGridY = -1;
  private pendingGridX = -1;
  private pendingGridY = -1;
  private pendingSinceMs = 0;
  private transitionStartedMs = -1;
  private elapsedMs = 0;
  private readonly viewport: { width: number; height: number };
  private readonly worldSize: { width: number; height: number };

  constructor(spec: GardenRenderSpec, mapTexture: Texture) {
    this.container.label = "musegarden-world";
    this.world.label = "world-camera-content";
    // GardenRenderSpec remains the source of dynamic flowers, but its temporary
    // grass background and Step 10 prototype field are replaced by the map art.
    this.garden = createGardenScene(spec, { includeBackground: false });
    this.cellSize = spec.cell_size;
    this.viewport = gardenViewportSize(spec);
    this.worldSize = mapWorldContentSize();
    const mapArt = createMapArt(mapTexture);
    this.garden.container.position.set(0, 0);
    this.entities.position.set(0, 0);
    this.entities.label = "world-entities";
    this.outgoingCellHighlight.label = "previous-player-cell-highlight";
    this.outgoingCellHighlight.alpha = 0;
    this.cellHighlight.label = "player-cell-highlight";
    this.entities.addChild(this.outgoingCellHighlight, this.cellHighlight);
    this.world.addChild(mapArt, this.garden.container, this.entities);
    this.container.addChild(this.world);
  }

  /** Focus the viewport without mutating any Player, flower, or plot world coordinate. */
  setCameraTarget(playerX: number, playerY: number): void {
    const camera = cameraPositionFor(
      { x: playerX, y: playerY },
      {
        width: this.viewport.width / MAP_VIEW_ZOOM,
        height: this.viewport.height / MAP_VIEW_ZOOM,
      },
      this.worldSize,
    );
    this.world.scale.set(MAP_VIEW_ZOOM);
    this.world.position.set(-camera.x * MAP_VIEW_ZOOM, -camera.y * MAP_VIEW_ZOOM);
  }

  setPlayerCell(playerX: number, playerY: number): void {
    const gridX = Math.floor(playerX / this.cellSize);
    const gridY = Math.floor(playerY / this.cellSize);
    if (this.highlightedGridX < 0) {
      this.highlightedGridX = gridX;
      this.highlightedGridY = gridY;
      this.pendingGridX = gridX;
      this.pendingGridY = gridY;
      this.drawCell(this.cellHighlight, gridX, gridY);
      this.cellHighlight.alpha = 1;
      return;
    }
    if (gridX === this.pendingGridX && gridY === this.pendingGridY) return;
    this.pendingGridX = gridX;
    this.pendingGridY = gridY;
    this.pendingSinceMs = this.elapsedMs;
  }

  private drawCell(graphics: Graphics, gridX: number, gridY: number): void {
    const inset = 2;
    const left = gridX * this.cellSize + inset;
    const top = gridY * this.cellSize + inset;
    const right = (gridX + 1) * this.cellSize - inset;
    const bottom = (gridY + 1) * this.cellSize - inset;
    graphics.clear()
      .rect(left, top, right - left, bottom - top)
      .fill({ color: "#eee8cf", alpha: 0.03 });
    this.drawDashedLine(graphics, left, top, right, top);
    this.drawDashedLine(graphics, right, top, right, bottom);
    this.drawDashedLine(graphics, right, bottom, left, bottom);
    this.drawDashedLine(graphics, left, bottom, left, top);
    graphics.stroke({ color: "#eee8cf", alpha: 0.3, width: 1.35 });
  }

  private drawDashedLine(graphics: Graphics, fromX: number, fromY: number, toX: number, toY: number): void {
    const length = Math.hypot(toX - fromX, toY - fromY);
    const directionX = (toX - fromX) / length;
    const directionY = (toY - fromY) / length;
    for (let distance = 0; distance < length; distance += CELL_DASH_LENGTH + CELL_DASH_GAP) {
      const dashEnd = Math.min(length, distance + CELL_DASH_LENGTH);
      graphics
        .moveTo(fromX + directionX * distance, fromY + directionY * distance)
        .lineTo(fromX + directionX * dashEnd, fromY + directionY * dashEnd);
    }
  }

  update(elapsedMs: number): void {
    this.elapsedMs = elapsedMs;
    this.garden.update(elapsedMs);
    if ((this.pendingGridX !== this.highlightedGridX || this.pendingGridY !== this.highlightedGridY) &&
        elapsedMs - this.pendingSinceMs >= CELL_STABILITY_MS) {
      this.drawCell(this.outgoingCellHighlight, this.highlightedGridX, this.highlightedGridY);
      this.outgoingCellHighlight.alpha = 1;
      this.highlightedGridX = this.pendingGridX;
      this.highlightedGridY = this.pendingGridY;
      this.drawCell(this.cellHighlight, this.highlightedGridX, this.highlightedGridY);
      this.cellHighlight.alpha = 0;
      this.transitionStartedMs = elapsedMs;
    }
    if (this.transitionStartedMs < 0) return;
    const progress = Math.min(1, (elapsedMs - this.transitionStartedMs) / CELL_CROSSFADE_MS);
    const eased = progress * progress * (3 - 2 * progress);
    this.outgoingCellHighlight.alpha = 1 - eased;
    this.cellHighlight.alpha = eased;
    if (progress === 1) {
      this.outgoingCellHighlight.clear();
      this.outgoingCellHighlight.alpha = 0;
      this.transitionStartedMs = -1;
    }
  }

  destroy(): void {
    this.world.removeChild(this.garden.container);
    this.garden.destroy();
    this.container.destroy({ children: true });
  }
}

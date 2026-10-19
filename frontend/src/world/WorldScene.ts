import { Container, Graphics } from "pixi.js";

import { createGardenScene, type PixelGarden } from "../rendering/flowers/gardenRenderer";
import type { GardenRenderSpec } from "../rendering/flowers/types";
import { cameraPositionFor } from "./Camera";
import { PLOT_COLUMNS, PLOT_ROWS, plotCellBounds, standardPlotBounds } from "./PlotCalibration";

const CELL_STABILITY_MS = 45;
const CELL_CROSSFADE_MS = 125;
const CELL_DASH_LENGTH = 6;
const CELL_DASH_GAP = 5;
export const WORLD_EDGE_PADDING = 36;
export const TEMPORARY_WORLD_MULTIPLIER = 2;

export function gardenViewportSize(spec: GardenRenderSpec): { width: number; height: number } {
  return {
    width: spec.pixel_width + WORLD_EDGE_PADDING * 2,
    height: spec.pixel_height + WORLD_EDGE_PADDING * 2,
  };
}

export function expandedWorldSize(spec: GardenRenderSpec): { width: number; height: number } {
  return {
    width: spec.pixel_width * TEMPORARY_WORLD_MULTIPLIER + WORLD_EDGE_PADDING * 2,
    height: spec.pixel_height * TEMPORARY_WORLD_MULTIPLIER + WORLD_EDGE_PADDING * 2,
  };
}

export function expandedWorldContentSize(spec: GardenRenderSpec): { width: number; height: number } {
  return {
    width: spec.pixel_width * TEMPORARY_WORLD_MULTIPLIER,
    height: spec.pixel_height * TEMPORARY_WORLD_MULTIPLIER,
  };
}

function createExtendedGround(spec: GardenRenderSpec, width: number, height: number): Graphics {
  const ground = new Graphics().rect(0, 0, width, height).fill(spec.background.base_color);
  const columns = Math.ceil(width / spec.cell_size);
  const rows = Math.ceil(height / spec.cell_size);
  for (let y = 0; y < rows; y += 1) {
    for (let x = 0; x < columns; x += 1) {
      if ((x + y) % 2 === 0) {
        ground.rect(x * spec.cell_size, y * spec.cell_size, spec.cell_size, spec.cell_size)
          .fill({ color: spec.background.tile_color, alpha: 0.2 });
      }
      if ((x * 17 + y * 29) % 7 === 0) {
        ground.rect(x * spec.cell_size + 9, y * spec.cell_size + 14, 3, 2)
          .fill({ color: spec.background.accent_color, alpha: 0.5 });
      }
    }
  }
  return ground;
}

/** Owns Pixi display layers; future world entities belong in entities. */
export class WorldScene {
  readonly container = new Container();
  readonly entities = new Container();
  private readonly world = new Container();
  private garden: PixelGarden;
  private readonly calibrationPlot = new Graphics();
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

  constructor(spec: GardenRenderSpec) {
    this.container.label = "musegarden-world";
    this.world.label = "world-camera-content";
    this.garden = createGardenScene(spec);
    this.cellSize = spec.cell_size;
    this.viewport = gardenViewportSize(spec);
    this.worldSize = expandedWorldSize(spec);
    const outerGround = createExtendedGround(spec, this.worldSize.width, this.worldSize.height);
    outerGround.label = "garden-edge-ground";
    this.garden.container.position.set(WORLD_EDGE_PADDING, WORLD_EDGE_PADDING);
    this.entities.position.set(WORLD_EDGE_PADDING, WORLD_EDGE_PADDING);
    this.entities.label = "world-entities";
    this.calibrationPlot.label = "plot-scale-calibration-3x2";
    this.drawCalibrationPlot(spec.pixel_width, spec.pixel_height);
    this.calibrationPlot.position.set(WORLD_EDGE_PADDING, WORLD_EDGE_PADDING);
    this.outgoingCellHighlight.label = "previous-player-cell-highlight";
    this.outgoingCellHighlight.alpha = 0;
    this.cellHighlight.label = "player-cell-highlight";
    this.entities.addChild(this.outgoingCellHighlight, this.cellHighlight);
    this.world.addChild(outerGround, this.garden.container, this.calibrationPlot, this.entities);
    this.container.addChild(this.world);
  }

  /** Focus the viewport without mutating any Player, flower, or plot world coordinate. */
  setCameraTarget(playerX: number, playerY: number): void {
    const camera = cameraPositionFor(
      { x: playerX + WORLD_EDGE_PADDING, y: playerY + WORLD_EDGE_PADDING },
      this.viewport,
      this.worldSize,
    );
    this.world.position.set(-camera.x, -camera.y);
  }

  /** A single visual 3 × 2 reference field for Step 10; it has no game state. */
  private drawCalibrationPlot(worldWidth: number, worldHeight: number): void {
    const plot = standardPlotBounds(worldWidth, worldHeight);
    this.calibrationPlot
      .rect(plot.x + 4, plot.y + 6, plot.width, plot.height)
      .fill({ color: "#183022", alpha: 0.32 })
      .rect(plot.x, plot.y, plot.width, plot.height)
      .fill("#c49352")
      .rect(plot.x + 4, plot.y + 4, plot.width - 8, plot.height - 8)
      .fill("#d6aa62");

    for (let row = 0; row < PLOT_ROWS; row += 1) {
      for (let column = 0; column < PLOT_COLUMNS; column += 1) {
        const cell = plotCellBounds(column, row, plot);
        this.calibrationPlot
          .rect(cell.x + 3, cell.y + 4, cell.width, cell.height)
          .fill({ color: "#4a3020", alpha: 0.35 })
          .rect(cell.x, cell.y, cell.width, cell.height)
          .fill("#725039")
          .rect(cell.x + 4, cell.y + 4, cell.width - 8, cell.height - 8)
          .fill("#805a3e");
        // Restrained pixel texture keeps the field readable without introducing new art assets.
        this.calibrationPlot
          .rect(cell.x + 13, cell.y + 17, 4, 3).fill({ color: "#9a7150", alpha: 0.55 })
          .rect(cell.x + cell.width - 21, cell.y + 34, 3, 4).fill({ color: "#523624", alpha: 0.5 })
          .rect(cell.x + 29, cell.y + cell.height - 18, 5, 3).fill({ color: "#a27550", alpha: 0.4 });
      }
    }
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

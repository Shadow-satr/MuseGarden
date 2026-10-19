/**
 * Step 10's single field is deliberately a visual calibration reference.
 * It does not replace GardenRenderSpec's 48px backend grid or create new
 * planting coordinates. Step 11 can reuse these values when the world grows.
 */
export const PLOT_COLUMNS = 3;
export const PLOT_ROWS = 2;
// A soil cell is one flower's planting place. Keep the established 48px
// garden-cell scale and the existing 58px player rather than enlarging either.
export const PLOT_CELL_SIZE = 48;
export const PLOT_CELL_GAP = 8;
export const PLOT_EDGE_PADDING = 18;
export const CALIBRATED_PLAYER_HEIGHT = 58;
export const PLAYER_TO_PLOT_CELL_RATIO = CALIBRATED_PLAYER_HEIGHT / PLOT_CELL_SIZE;

export interface PlotBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export function standardPlotBounds(worldWidth: number, worldHeight: number): PlotBounds {
  const width = PLOT_EDGE_PADDING * 2 + PLOT_COLUMNS * PLOT_CELL_SIZE + (PLOT_COLUMNS - 1) * PLOT_CELL_GAP;
  const height = PLOT_EDGE_PADDING * 2 + PLOT_ROWS * PLOT_CELL_SIZE + (PLOT_ROWS - 1) * PLOT_CELL_GAP;
  return {
    x: Math.round((worldWidth - width) / 2),
    y: Math.round((worldHeight - height) / 2),
    width,
    height,
  };
}

export function plotCellBounds(column: number, row: number, plot: PlotBounds): PlotBounds {
  return {
    x: plot.x + PLOT_EDGE_PADDING + column * (PLOT_CELL_SIZE + PLOT_CELL_GAP),
    y: plot.y + PLOT_EDGE_PADDING + row * (PLOT_CELL_SIZE + PLOT_CELL_GAP),
    width: PLOT_CELL_SIZE,
    height: PLOT_CELL_SIZE,
  };
}

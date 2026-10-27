/**
 * Step 10's single field is deliberately a visual calibration reference.
 * It does not replace GardenRenderSpec's 48px backend grid or create new
 * planting coordinates. Step 11 can reuse these values when the world grows.
 */
export const PLOT_COLUMNS = 3;
export const PLOT_ROWS = 2;
// Each map grid has one quarter of the original area, so its side length is
// half the original preview grid. The visible map remains unlined.
export const PLOT_CELL_SIZE = 16;
export const PLOT_CELL_GAP = 2;
export const PLOT_EDGE_PADDING = 6;
export const CALIBRATED_PLAYER_HEIGHT = 30;
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

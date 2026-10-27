import { describe, expect, it } from "vitest";

import {
  CALIBRATED_PLAYER_HEIGHT,
  PLAYER_TO_PLOT_CELL_RATIO,
  PLOT_CELL_SIZE,
  plotCellBounds,
  standardPlotBounds,
} from "./PlotCalibration";

describe("Step 10 plot calibration", () => {
  it("keeps a centred 3 by 2 field large enough to inspect in the current world", () => {
    const plot = standardPlotBounds(768, 480);
    expect(plot.width).toBe(64);
    expect(plot.height).toBe(46);
    expect(plot.x).toBe(352);
    expect(plot.y).toBe(217);
    expect(plot.width / 768).toBeLessThan(0.15);
  });

  it("uses evenly sized cells and a player slightly taller than one cell", () => {
    const plot = standardPlotBounds(768, 480);
    const first = plotCellBounds(0, 0, plot);
    const last = plotCellBounds(2, 1, plot);
    expect(first.width).toBe(PLOT_CELL_SIZE);
    expect(first.height).toBe(PLOT_CELL_SIZE);
    expect(last.x).toBeGreaterThan(first.x);
    expect(last.y).toBeGreaterThan(first.y);
    expect(CALIBRATED_PLAYER_HEIGHT).toBe(30);
    expect(CALIBRATED_PLAYER_HEIGHT / PLOT_CELL_SIZE).toBeCloseTo(PLAYER_TO_PLOT_CELL_RATIO, 2);
  });
});

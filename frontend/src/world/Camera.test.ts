import { describe, expect, it } from "vitest";

import { cameraPositionFor } from "./Camera";

describe("cameraPositionFor", () => {
  const viewport = { width: 840, height: 552 };
  const world = { width: 1608, height: 1032 };

  it("keeps the view at the top-left until centering is possible", () => {
    expect(cameraPositionFor({ x: 420, y: 276 }, viewport, world)).toEqual({ x: 0, y: 0 });
  });

  it("follows a world-space focus point through the middle of the world", () => {
    expect(cameraPositionFor({ x: 804, y: 516 }, viewport, world)).toEqual({ x: 384, y: 240 });
  });

  it("clamps every side to the world without exposing an empty region", () => {
    expect(cameraPositionFor({ x: -50, y: -20 }, viewport, world)).toEqual({ x: 0, y: 0 });
    expect(cameraPositionFor({ x: 9999, y: 9999 }, viewport, world)).toEqual({ x: 768, y: 480 });
  });
});

export interface CameraSize {
  width: number;
  height: number;
}

export interface CameraPosition {
  x: number;
  y: number;
}

/**
 * Converts a world-space focus point into a clamped camera position.
 * The camera moves content only; callers retain their original world values.
 */
export function cameraPositionFor(
  focus: CameraPosition,
  viewport: CameraSize,
  world: CameraSize,
): CameraPosition {
  const maxX = Math.max(0, world.width - viewport.width);
  const maxY = Math.max(0, world.height - viewport.height);
  return {
    x: Math.max(0, Math.min(maxX, Math.round(focus.x - viewport.width / 2))),
    y: Math.max(0, Math.min(maxY, Math.round(focus.y - viewport.height / 2))),
  };
}

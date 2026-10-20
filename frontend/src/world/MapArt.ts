/**
 * The supplied full-garden artwork is the world itself. These dimensions come
 * from the original PNG, so camera bounds never stretch or crop the artwork.
 */
export const MAP_ART_WIDTH = 1448;
export const MAP_ART_HEIGHT = 1086;

export const MAP_ART_SIZE = {
  width: MAP_ART_WIDTH,
  height: MAP_ART_HEIGHT,
} as const;
import { Assets, Texture } from "pixi.js";


const MAP_ART_URL = new URL("../assets/musegarden-map.png", import.meta.url).href;

/** Load before scene construction so the first rendered frame is the real map. */
export function loadMapArtTexture(): Promise<Texture> {
  return Assets.load<Texture>(MAP_ART_URL);
}

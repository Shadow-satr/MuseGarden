import { Assets, type Texture } from "pixi.js";

const GRASS_A_URL = new URL("../assets/third-party/mini-meadow/grass_a.png", import.meta.url).href;
const GRASS_B_URL = new URL("../assets/third-party/mini-meadow/grass_b.png", import.meta.url).href;
const DIRT_URL = new URL("../assets/third-party/mini-meadow/dirt.png", import.meta.url).href;
const WATER_URL = new URL("../assets/third-party/mini-meadow/water_1.png", import.meta.url).href;

export interface TerrainTextures {
  readonly grass: readonly [Texture, Texture];
  readonly path: Texture;
  readonly water: Texture;
}

/** Loads the small shared terrain texture set once with crisp pixel filtering. */
export async function loadTerrainTextures(): Promise<TerrainTextures> {
  const [grassA, grassB, path, water] = await Promise.all([
    Assets.load<Texture>({ src: GRASS_A_URL, data: { scaleMode: "nearest" } }),
    Assets.load<Texture>({ src: GRASS_B_URL, data: { scaleMode: "nearest" } }),
    Assets.load<Texture>({ src: DIRT_URL, data: { scaleMode: "nearest" } }),
    Assets.load<Texture>({ src: WATER_URL, data: { scaleMode: "nearest" } }),
  ]);
  return { grass: [grassA, grassB], path, water };
}

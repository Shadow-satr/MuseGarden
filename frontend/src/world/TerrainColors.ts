import type { TerrainType } from "./TerrainMap";

/** Shared simplified colours for non-textured terrain and map previews. */
export const TERRAIN_COLORS: Record<TerrainType, string> = {
  GRASS: "#4e8558",
  PATH: "#c9a56b",
  WATER: "#3d84ad",
  SOIL: "#74513c",
  STRUCTURE: "#625b53",
  BRIDGE: "#a97a4e",
  TREE: "#285439",
};

/** Shared, restrained pixel-art palette for terrain features drawn with Pixi Graphics. */
export const TERRAIN_FEATURE_COLORS = {
  bridgeOutline: "#3b2b25",
  bridgeDeck: "#a97242",
  bridgePlank: "#70452f",
  bridgeHighlight: "#c9955d",
  structureOutline: "#302b31",
  // A warmer roof family keeps structures distinct without becoming cold, heavy grey blocks.
  structureRoof: "#6d6259",
  structureRoofLight: "#88796d",
  structureRoofShade: "#514946",
  structureEntry: "#b88454",
} as const;

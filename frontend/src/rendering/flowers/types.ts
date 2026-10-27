export type FlowerSpecies =
  | "rose"
  | "peony"
  | "sunflower"
  | "tulip"
  | "hydrangea"
  | "lily"
  | "daisy"
  | "lavender"
  | "wildflower";

export type BloomShape =
  | "rosette"
  | "rounded_layered"
  | "radial_disc"
  | "cup"
  | "clustered_sphere"
  | "trumpet"
  | "spike_cluster"
  | "open_cluster";

export type LeafShape =
  | "serrated"
  | "broad_lobed"
  | "broad_heart"
  | "lance"
  | "broad_oval"
  | "narrow"
  | "mixed";

export type ParticleEffect =
  | "none"
  | "soft_glow"
  | "sparkles"
  | "petals"
  | "fireflies"
  | "stardust";

export type FlowerDecoration =
  | "none"
  | "dew_drops"
  | "leaf_sprigs"
  | "star_charms"
  | "light_ribbons";

export type GrowthDirection =
  | "steady"
  | "upright"
  | "opening"
  | "expanding"
  | "rising"
  | "releasing";

export type FlowerSize = "small" | "large";

export const RENDER_LAYER_ORDER = [
  "shadow",
  "stem",
  "leaves",
  "bloom_back",
  "bloom_front",
  "decoration",
  "glow",
  "particles",
] as const;

export type RenderLayer = (typeof RENDER_LAYER_ORDER)[number];

export interface FlowerColorSpec {
  petal_primary: string;
  petal_secondary: string;
  petal_highlight: string;
  flower_center: string;
  stem: string;
  leaf: string;
  glow: string;
  particle: string;
}

export interface FlowerGeometrySpec {
  bloom_shape: BloomShape;
  leaf_shape: LeafShape;
  petal_count: number;
  bloom_scale_x: number;
  bloom_scale_y: number;
  stem_height_ratio: number;
  stem_curve: number;
  leaf_count: number;
  leaf_angle_offset: number;
  anchor_x: 0.5;
  anchor_y: 1;
}

export interface FlowerAnimationSpec {
  sway_amplitude: number;
  sway_period_ms: number;
  sway_phase: number;
  glow_opacity: number;
  glow_radius_ratio: number;
  particle_rate: number;
  particle_phase: number;
}

export interface FlowerRenderSpec {
  renderer_schema_version: "1.0";
  template_id: string;
  species: FlowerSpecies;
  variation_seed: number | string;
  colors: FlowerColorSpec;
  geometry: FlowerGeometrySpec;
  animation: FlowerAnimationSpec;
  particle_effect: ParticleEffect;
  decoration: FlowerDecoration;
  growth_direction: GrowthDirection;
  layer_order: RenderLayer[];
}

export interface FlowerPreviewGroup {
  species: FlowerSpecies;
  display_name: string;
  variants: FlowerRenderSpec[];
}

export interface GardenBackgroundSpec {
  style: "meadow";
  base_color: string;
  tile_color: string;
  accent_color: string;
}

export interface GardenRenderFlower {
  planting_record_id: string;
  flower_artifact_id: string;
  template_id: string;
  grid_x: number;
  grid_y: number;
  pixel_x: number;
  pixel_y: number;
  scale: number;
  z_index: number;
  placement_schema_version?: "legacy" | "terrain-v1";
  flower_size?: FlowerSize;
  occupied_tiles?: [number, number][];
  render_spec: FlowerRenderSpec;
}

export interface GardenRenderSpec {
  renderer_schema_version: "1.0";
  garden_id: string;
  grid_width: number;
  grid_height: number;
  cell_size: number;
  pixel_width: number;
  pixel_height: number;
  background: GardenBackgroundSpec;
  flowers: GardenRenderFlower[];
}


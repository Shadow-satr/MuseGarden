import {
  RENDER_LAYER_ORDER,
  type FlowerRenderSpec,
  type GardenRenderSpec,
  type RenderLayer,
} from "./types";

const HEX_COLOR = /^#[0-9A-F]{6}$/;
const SPECIES = new Set([
  "rose",
  "peony",
  "sunflower",
  "tulip",
  "hydrangea",
  "lily",
  "daisy",
  "lavender",
  "wildflower",
]);
const BLOOM_SHAPES = new Set([
  "rosette", "rounded_layered", "radial_disc", "cup", "clustered_sphere",
  "trumpet", "spike_cluster", "open_cluster",
]);
const LEAF_SHAPES = new Set([
  "serrated", "broad_lobed", "broad_heart", "lance", "broad_oval", "narrow", "mixed",
]);
const PARTICLE_EFFECTS = new Set(["none", "soft_glow", "sparkles", "petals", "fireflies", "stardust"]);
const DECORATIONS = new Set(["none", "dew_drops", "leaf_sprigs", "star_charms", "light_ribbons"]);
const GROWTH_DIRECTIONS = new Set(["steady", "upright", "opening", "expanding", "rising", "releasing"]);

const isNumberInRange = (value: unknown, min: number, max: number) =>
  typeof value === "number" && Number.isFinite(value) && value >= min && value <= max;

const isVariationSeed = (value: unknown) =>
  (typeof value === "number" && Number.isSafeInteger(value) && value >= 0) ||
  (typeof value === "string" && /^(0|[1-9][0-9]*)$/.test(value) &&
    BigInt(value) <= 9_223_372_036_854_775_807n);

export function assertFlowerRenderSpec(value: unknown): asserts value is FlowerRenderSpec {
  if (!value || typeof value !== "object") throw new Error("RenderSpec 必须是对象");
  const spec = value as Record<string, any>;

  if (spec.renderer_schema_version !== "1.0") throw new Error("不支持的 Renderer Schema");
  if (!SPECIES.has(spec.species)) throw new Error("不支持的花型");
  if (spec.template_id !== `${spec.species}_v1`) throw new Error("template_id 与花型不一致");
  if (!isVariationSeed(spec.variation_seed)) {
    throw new Error("variation_seed 无效");
  }

  const colors = spec.colors as Record<string, unknown> | undefined;
  const colorKeys = [
    "petal_primary", "petal_secondary", "petal_highlight", "flower_center",
    "stem", "leaf", "glow", "particle",
  ];
  if (!colors || colorKeys.some((key) => !HEX_COLOR.test(String(colors[key])))) {
    throw new Error("颜色必须使用大写 #RRGGBB");
  }

  const geometry = spec.geometry as Record<string, unknown> | undefined;
  if (
    !geometry ||
    typeof geometry.bloom_shape !== "string" ||
    !BLOOM_SHAPES.has(geometry.bloom_shape) ||
    typeof geometry.leaf_shape !== "string" ||
    !LEAF_SHAPES.has(geometry.leaf_shape) ||
    !Number.isInteger(geometry.petal_count) ||
    !isNumberInRange(geometry.petal_count, 3, 16) ||
    !isNumberInRange(geometry.bloom_scale_x, 0.5, 1.5) ||
    !isNumberInRange(geometry.bloom_scale_y, 0.5, 1.5) ||
    !isNumberInRange(geometry.stem_height_ratio, 0, 1) ||
    !isNumberInRange(geometry.stem_curve, -1, 1) ||
    !Number.isInteger(geometry.leaf_count) ||
    !isNumberInRange(geometry.leaf_count, 2, 5) ||
    !isNumberInRange(geometry.leaf_angle_offset, -15, 15) ||
    geometry.anchor_x !== 0.5 || geometry.anchor_y !== 1
  ) throw new Error("几何参数无效");

  const animation = spec.animation as Record<string, unknown> | undefined;
  if (
    !animation ||
    !isNumberInRange(animation.sway_amplitude, 0, 0.1) ||
    !isNumberInRange(animation.sway_period_ms, 1200, 3600) ||
    !isNumberInRange(animation.sway_phase, 0, 1) ||
    !isNumberInRange(animation.glow_opacity, 0, 0.65) ||
    !isNumberInRange(animation.glow_radius_ratio, 0, 0.18) ||
    !isNumberInRange(animation.particle_rate, 0, 5) ||
    !isNumberInRange(animation.particle_phase, 0, 1)
  ) throw new Error("动画参数无效");

  if (
    !PARTICLE_EFFECTS.has(spec.particle_effect) ||
    !DECORATIONS.has(spec.decoration) ||
    !GROWTH_DIRECTIONS.has(spec.growth_direction)
  ) throw new Error("视觉 token 无效");

  const layers = spec.layer_order as RenderLayer[] | undefined;
  if (!layers || layers.length !== RENDER_LAYER_ORDER.length ||
      layers.some((layer, index) => layer !== RENDER_LAYER_ORDER[index])) {
    throw new Error("图层顺序无效");
  }
}

export function assertGardenRenderSpec(value: unknown): asserts value is GardenRenderSpec {
  if (!value || typeof value !== "object") throw new Error("GardenRenderSpec 必须是对象");
  const spec = value as Record<string, any>;
  if (spec.renderer_schema_version !== "1.0") throw new Error("不支持的 Garden Renderer Schema");
  if (typeof spec.garden_id !== "string" || spec.garden_id.length === 0) throw new Error("garden_id 无效");
  if (!Number.isInteger(spec.grid_width) || spec.grid_width <= 0 ||
      !Number.isInteger(spec.grid_height) || spec.grid_height <= 0) {
    throw new Error("花园网格尺寸无效");
  }
  if (!Number.isInteger(spec.cell_size) || spec.cell_size < 24 || spec.cell_size > 96) {
    throw new Error("cell_size 无效");
  }
  if (spec.pixel_width !== spec.grid_width * spec.cell_size ||
      spec.pixel_height !== spec.grid_height * spec.cell_size) {
    throw new Error("花园像素尺寸无效");
  }
  const background = spec.background as Record<string, unknown> | undefined;
  if (!background || background.style !== "meadow" ||
      !HEX_COLOR.test(String(background.base_color)) ||
      !HEX_COLOR.test(String(background.tile_color)) ||
      !HEX_COLOR.test(String(background.accent_color))) {
    throw new Error("花园背景无效");
  }
  if (!Array.isArray(spec.flowers)) throw new Error("flowers 必须是数组");

  let lastZIndex = -1;
  const occupied = new Set<string>();
  for (const flower of spec.flowers as Array<Record<string, any>>) {
    assertFlowerRenderSpec(flower.render_spec);
    if (flower.template_id !== flower.render_spec.template_id) throw new Error("花园花朵模板不一致");
    if (!Number.isInteger(flower.grid_x) || flower.grid_x < 0 || flower.grid_x >= spec.grid_width ||
        !Number.isInteger(flower.grid_y) || flower.grid_y < 0 || flower.grid_y >= spec.grid_height) {
      throw new Error("花园花朵网格坐标无效");
    }
    if (!isNumberInRange(flower.pixel_x, 0, spec.pixel_width) ||
        !isNumberInRange(flower.pixel_y, 0, spec.pixel_height) ||
        !isNumberInRange(flower.scale, 0.75, 1.25) ||
        !Number.isInteger(flower.z_index) || flower.z_index < lastZIndex) {
      throw new Error("花园花朵渲染参数无效");
    }
    const position = `${flower.grid_x}:${flower.grid_y}`;
    if (occupied.has(position)) throw new Error("花园存在重复位置");
    occupied.add(position);
    lastZIndex = flower.z_index;
  }
}

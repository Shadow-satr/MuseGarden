import { Container, Graphics } from "pixi.js";

import type { FlowerRenderSpec, FlowerSpecies } from "./types";

export const FLOWER_WIDTH = 48;
export const FLOWER_HEIGHT = 64;
const CENTER_X = 24;
const GROUND_Y = 58;

type Layers = Record<"stem" | "leaves" | "bloom_back" | "bloom_front", Container>;

const block = (graphics: Graphics, x: number, y: number, w: number, h: number, color: string) => {
  graphics.rect(Math.round(x), Math.round(y), Math.max(1, Math.round(w)), Math.max(1, Math.round(h))).fill(color);
};

function drawStem(spec: FlowerRenderSpec, layers: Layers) {
  const graphics = new Graphics();
  const stemTop = Math.round(GROUND_Y - 23 * spec.geometry.stem_height_ratio);
  const bend = Math.round(spec.geometry.stem_curve * 3);
  for (let y = GROUND_Y; y >= stemTop; y -= 2) {
    const progress = (GROUND_Y - y) / Math.max(1, GROUND_Y - stemTop);
    block(graphics, CENTER_X + bend * progress - 1, y, 2, 2, spec.colors.stem);
  }
  layers.stem.addChild(graphics);
  return { stemTop, bloomX: CENTER_X + bend };
}

function drawLeaves(spec: FlowerRenderSpec, layers: Layers, stemTop: number) {
  const graphics = new Graphics();
  const stemSpan = GROUND_Y - stemTop;
  for (let index = 0; index < spec.geometry.leaf_count; index += 1) {
    const progress = (index + 1) / (spec.geometry.leaf_count + 1);
    const y = GROUND_Y - stemSpan * progress;
    const side = index % 2 === 0 ? -1 : 1;
    const reach = spec.geometry.leaf_shape === "broad_heart" || spec.geometry.leaf_shape === "broad_oval" ? 8 : 6;
    const outerWidth = reach;
    const innerWidth = Math.max(2, reach - 3);
    block(graphics, side < 0 ? CENTER_X - outerWidth : CENTER_X + 2, y, outerWidth, 2, spec.colors.leaf);
    block(graphics, side < 0 ? CENTER_X - innerWidth : CENTER_X + 4, y - 2, innerWidth, 2, spec.colors.leaf);
  }
  layers.leaves.addChild(graphics);
}

function petal(graphics: Graphics, x: number, y: number, w: number, h: number, color: string) {
  // Stepped shoulders give even the smallest petals a readable silhouette.
  block(graphics, x - w / 2 + 1, y - h / 2, w - 2, h, color);
  block(graphics, x - w / 2, y - h / 2 + 1, w, h - 2, color);
}

function drawRadial(spec: FlowerRenderSpec, back: Graphics, front: Graphics, x: number, y: number, long = false) {
  const count = Math.min(16, Math.max(6, spec.geometry.petal_count));
  const radiusX = (long ? 9 : 7) * spec.geometry.bloom_scale_x;
  const radiusY = (long ? 8 : 6) * spec.geometry.bloom_scale_y;
  for (let index = 0; index < count; index += 1) {
    const angle = (Math.PI * 2 * index) / count;
    const target = index < count / 2 ? back : front;
    petal(target, x + Math.cos(angle) * radiusX, y + Math.sin(angle) * radiusY, long ? 4 : 5, long ? 7 : 5, index % 3 === 0 ? spec.colors.petal_highlight : spec.colors.petal_primary);
    const foldX = x + Math.cos(angle) * radiusX * 0.70;
    const foldY = y + Math.sin(angle) * radiusY * 0.70;
    petal(target, foldX, foldY, 3, 3, spec.colors.petal_secondary);
    if (long) block(target, foldX, foldY - 1, 1, 2, spec.colors.flower_center);
  }
  block(front, x - 3, y - 3, 6, 6, spec.colors.flower_center);
  block(front, x - 1, y - 1, 2, 2, spec.colors.petal_secondary);
  block(front, x - 2, y - 2, 2, 1, spec.colors.petal_highlight);
}

function drawBloom(spec: FlowerRenderSpec, layers: Layers, x: number, y: number) {
  const back = new Graphics();
  const front = new Graphics();
  const sx = spec.geometry.bloom_scale_x;
  const sy = spec.geometry.bloom_scale_y;

  switch (spec.species) {
    case "rose":
    case "camellia":
      // Staggered pixel petals form a layered rosette, rather than nested rectangles.
      block(back, x - 8 * sx, y - 5 * sy, 16 * sx, 10 * sy, spec.colors.petal_secondary);
      block(back, x - 6 * sx, y - 8 * sy, 12 * sx, 16 * sy, spec.colors.petal_secondary);
      block(front, x - 7 * sx, y - 4 * sy, 4 * sx, 8 * sy, spec.colors.petal_primary);
      block(front, x + 3 * sx, y - 5 * sy, 4 * sx, 9 * sy, spec.colors.petal_primary);
      block(front, x - 5 * sx, y - 7 * sy, 10 * sx, 3 * sy, spec.colors.petal_highlight);
      block(front, x - 5 * sx, y + 4 * sy, 10 * sx, 3 * sy, spec.colors.petal_primary);
      block(front, x - 3 * sx, y - 3 * sy, 7 * sx, 6 * sy, spec.colors.petal_primary);
      block(front, x - 2 * sx, y - 2 * sy, 5 * sx, 2 * sy, spec.colors.petal_highlight);
      block(front, x + 1 * sx, y, 2 * sx, 3 * sy, spec.colors.petal_secondary);
      block(front, x - 2 * sx, y + 2 * sy, 4 * sx, 1 * sy, spec.colors.petal_highlight);
      block(front, x - 7 * sx, y - 4 * sy, 2 * sx, 3 * sy, spec.colors.petal_highlight);
      block(front, x + 4 * sx, y + 2 * sy, 3 * sx, sy, spec.colors.petal_secondary);
      break;
    case "peony":
      for (let index = 0; index < 12; index += 1) {
        const angle = (Math.PI * 2 * index) / 12;
        petal(index < 6 ? back : front, x + Math.cos(angle) * 6 * sx, y + Math.sin(angle) * 5 * sy, 6, 6, index % 2 ? spec.colors.petal_primary : spec.colors.petal_highlight);
      }
      block(front, x - 4, y - 4, 8, 8, spec.colors.petal_secondary);
      for (const [dx, dy] of [[-4, 1], [-2, -3], [2, -4], [4, 0], [1, 4]]) {
        petal(front, x + dx, y + dy, 5, 4, spec.colors.petal_primary);
        block(front, x + dx - 1, y + dy - 2, 2, 1, spec.colors.petal_highlight);
      }
      block(front, x - 2, y - 2, 4, 4, spec.colors.flower_center);
      break;
    case "sunflower":
      for (let index = 0; index < 12; index += 1) {
        const angle = Math.PI * 2 * index / 12;
        const px = x + Math.cos(angle) * 8 * sx;
        const py = y + Math.sin(angle) * 7 * sy;
        const vertical = Math.abs(Math.sin(angle)) > .7;
        block(back, px - (vertical ? 2 : 3), py - (vertical ? 3 : 2), vertical ? 4 : 6, vertical ? 6 : 4, spec.colors.petal_secondary);
        block(front, px - (vertical ? 1 : 2), py - (vertical ? 2 : 1), vertical ? 2 : 4, vertical ? 4 : 2, index % 3 === 0 ? spec.colors.petal_highlight : spec.colors.petal_primary);
      }
      for (let index = 0; index < 10; index++) {
        const angle = Math.PI * 2 * (index + 0.5) / 10;
        petal(front, x + Math.cos(angle) * 5.8 * sx, y + Math.sin(angle) * 5.6 * sy,
          4, 4, index < 5 ? spec.colors.petal_primary : spec.colors.petal_highlight);
      }
      block(front, x - 5, y - 4, 10, 8, spec.colors.flower_center);
      block(front, x - 4, y - 5, 8, 10, spec.colors.flower_center);
      for (const [dx, dy] of [[-2, -2], [1, -2], [-3, 1], [0, 1], [3, 1], [-1, 3]] as const) {
        block(front, x + dx, y + dy, 1, 1, spec.colors.petal_secondary);
      }
      break;
    case "tulip":
      block(back, x - 8 * sx, y - 7 * sy, 16 * sx, 10 * sy, spec.colors.petal_secondary);
      block(front, x - 6 * sx, y - 9 * sy, 5 * sx, 12 * sy, spec.colors.petal_primary);
      block(front, x - 1 * sx, y - 7 * sy, 6 * sx, 11 * sy, spec.colors.petal_highlight);
      block(front, x + 4 * sx, y - 9 * sy, 4 * sx, 12 * sy, spec.colors.petal_primary);
      // A stepped diagonal lip folds the front petal over the cup.
      for (let row = 0; row < 4; row++) {
        block(front, x - (6 - row) * sx, y + (row - 2) * sy, (11 - row * 2) * sx, 2 * sy, spec.colors.petal_primary);
        block(front, x - (6 - row) * sx, y + (row - 2) * sy, 2 * sx, sy, spec.colors.petal_highlight);
      }
      break;
    case "hydrangea":
      for (let row = -2; row <= 2; row += 1) for (let col = -2; col <= 2; col += 1) {
        if (Math.abs(row) + Math.abs(col) > 3) continue;
        const px = x + (col * 4 + Math.abs(row % 2)) * sx;
        const py = y + row * 3.5 * sy;
        const cluster = row < 0 ? back : front;
        block(cluster, px - 2, py - 1, 5, 3, spec.colors.petal_secondary);
        block(cluster, px - 1, py - 2, 3, 5, spec.colors.petal_primary);
        block(cluster, px - 2, py - 1, 2, 2, spec.colors.petal_highlight);
        block(cluster, px, py, 1, 1, spec.colors.flower_center);
      }
      break;
    case "lily":
    case "lotus":
      drawRadial(spec, back, front, x, y, true);
      block(front, x - 2, y - 2, 4, 4, spec.colors.flower_center);
      break;
    case "daisy":
    case "aster":
      drawRadial(spec, back, front, x, y);
      break;
    case "lavender":
      for (const side of [-1, 1]) {
        for (let step = 0; step < 5; step++) {
          const px = x + side * (3 + step * 1.5) * sx;
          const py = y - (step * 2.5 + (side > 0 ? 2 : 0)) * sy;
          petal(back, px, py, 5, 4, spec.colors.petal_secondary);
          block(back, px - 1, py - 2, 3, 2, spec.colors.petal_primary);
        }
      }
      block(back, x - 1, y - 17 * sy, 2, 19 * sy, spec.colors.stem);
      for (let index = 0; index < 6; index += 1) {
        const yy = y - 16 * sy + index * 3 * sy;
        const spread = (2 + (index % 2)) * sx;
        block(back, x - spread - 2, yy, 4, 3, spec.colors.petal_secondary);
        block(front, x - spread - 1, yy - 1, 3, 2, spec.colors.petal_highlight);
        block(back, x + spread - 1, yy + 1, 4, 3, spec.colors.petal_primary);
        block(front, x + spread, yy + 1, 2, 2, spec.colors.petal_highlight);
      }
      block(front, x - 1, y - 19 * sy, 3, 3, spec.colors.petal_highlight);
      break;
    case "wildflower":
      drawRadial(spec, back, front, x - 5, y + 1, false);
      petal(front, x + 7, y - 4, 5, 5, spec.colors.petal_highlight);
      petal(front, x + 9, y + 2, 4, 4, spec.colors.petal_primary);
      break;
    case "cosmos":
      drawRadial(spec, back, front, x, y);
      break;
    case "poppy":
      for (const [dx, dy] of [[-5, -3], [5, -3], [-5, 3], [5, 3]]) {
        petal(back, x + dx * sx, y + dy * sy, 10, 9, spec.colors.petal_primary);
        block(front, x + dx * sx - 2, y + dy * sy - 3, 4, 2, spec.colors.petal_highlight);
      }
      block(front, x - 3, y - 3, 6, 6, spec.colors.flower_center);
      break;
    case "bellflower":
      for (const offset of [-6, 0, 6]) {
        const bx = x + offset * sx;
        const by = y + (offset === 0 ? -5 : 1) * sy;
        block(back, bx - 3, by - 4, 6, 7, spec.colors.petal_secondary);
        block(front, bx - 2, by - 4, 4, 7, spec.colors.petal_primary);
        block(front, bx - 4, by + 2, 8, 2, spec.colors.petal_highlight);
      }
      break;
    case "cherry_blossom":
      for (let index = 0; index < 5; index++) {
        const angle = Math.PI * 2 * index / 5 - Math.PI / 2;
        petal(back, x + Math.cos(angle) * 6 * sx, y + Math.sin(angle) * 6 * sy, 8, 8, spec.colors.petal_primary);
        petal(front, x + Math.cos(angle) * 6 * sx, y + Math.sin(angle) * 6 * sy, 4, 4, spec.colors.petal_highlight);
      }
      block(front, x - 2, y - 2, 4, 4, spec.colors.flower_center);
      break;
  }

  for (const bloom of [back, front]) {
    bloom.pivot.set(x, y);
    bloom.position.set(x, y);
    bloom.scale.set(1.65, 1.45);
  }
  layers.bloom_back.addChild(back);
  layers.bloom_front.addChild(front);
}

export function drawFlowerTemplate(spec: FlowerRenderSpec, layers: Layers) {
  const { stemTop, bloomX } = drawStem(spec, layers);
  drawLeaves(spec, layers, stemTop);
  drawBloom(spec, layers, bloomX, stemTop - 2);
  return { x: bloomX, y: stemTop - 2 };
}

export const TEMPLATE_IDS: Record<FlowerSpecies, string> = {
  rose: "rose_v1", peony: "peony_v1", sunflower: "sunflower_v1",
  tulip: "tulip_v1", hydrangea: "hydrangea_v1", lily: "lily_v1",
  daisy: "daisy_v1", lavender: "lavender_v1", wildflower: "wildflower_v1",
  cosmos: "cosmos_v1", poppy: "poppy_v1", bellflower: "bellflower_v1", cherry_blossom: "cherry_blossom_v1",
  camellia: "camellia_v1", aster: "aster_v1", lotus: "lotus_v1",
};

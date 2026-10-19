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
  const stemTop = Math.round(GROUND_Y - 34 * spec.geometry.stem_height_ratio);
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
  block(graphics, x - w / 2, y - h / 2, w, h, color);
  if (w >= 4 && h >= 4) block(graphics, x - w / 2 + 1, y - h / 2 + 1, w - 2, h - 2, color);
}

function drawRadial(spec: FlowerRenderSpec, back: Graphics, front: Graphics, x: number, y: number, long = false) {
  const count = Math.min(16, Math.max(6, spec.geometry.petal_count));
  const radiusX = (long ? 9 : 7) * spec.geometry.bloom_scale_x;
  const radiusY = (long ? 8 : 6) * spec.geometry.bloom_scale_y;
  for (let index = 0; index < count; index += 1) {
    const angle = (Math.PI * 2 * index) / count;
    const target = index < count / 2 ? back : front;
    petal(target, x + Math.cos(angle) * radiusX, y + Math.sin(angle) * radiusY, long ? 4 : 5, long ? 7 : 5, index % 3 === 0 ? spec.colors.petal_highlight : spec.colors.petal_primary);
  }
  block(front, x - 3, y - 3, 6, 6, spec.colors.flower_center);
  block(front, x - 1, y - 1, 2, 2, spec.colors.petal_secondary);
}

function drawBloom(spec: FlowerRenderSpec, layers: Layers, x: number, y: number) {
  const back = new Graphics();
  const front = new Graphics();
  const sx = spec.geometry.bloom_scale_x;
  const sy = spec.geometry.bloom_scale_y;

  switch (spec.species) {
    case "rose":
      for (let ring = 3; ring >= 1; ring -= 1) {
        const color = ring === 3 ? spec.colors.petal_secondary : ring === 2 ? spec.colors.petal_primary : spec.colors.petal_highlight;
        block(ring === 3 ? back : front, x - ring * 3 * sx, y - ring * 2 * sy, ring * 6 * sx, ring * 4 * sy, color);
      }
      block(front, x - 2, y - 2, 4, 4, spec.colors.flower_center);
      break;
    case "peony":
      for (let index = 0; index < 12; index += 1) {
        const angle = (Math.PI * 2 * index) / 12;
        petal(index < 6 ? back : front, x + Math.cos(angle) * 6 * sx, y + Math.sin(angle) * 5 * sy, 6, 6, index % 2 ? spec.colors.petal_primary : spec.colors.petal_highlight);
      }
      block(front, x - 4, y - 4, 8, 8, spec.colors.petal_secondary);
      block(front, x - 2, y - 2, 4, 4, spec.colors.flower_center);
      break;
    case "sunflower":
      drawRadial(spec, back, front, x, y, true);
      block(front, x - 4, y - 4, 8, 8, spec.colors.flower_center);
      block(front, x - 2, y - 2, 4, 4, spec.colors.petal_secondary);
      break;
    case "tulip":
      block(back, x - 8 * sx, y - 7 * sy, 16 * sx, 10 * sy, spec.colors.petal_secondary);
      block(front, x - 6 * sx, y - 9 * sy, 5 * sx, 12 * sy, spec.colors.petal_primary);
      block(front, x - 1 * sx, y - 7 * sy, 6 * sx, 11 * sy, spec.colors.petal_highlight);
      block(front, x + 4 * sx, y - 9 * sy, 4 * sx, 12 * sy, spec.colors.petal_primary);
      break;
    case "hydrangea":
      for (let row = -2; row <= 2; row += 1) for (let col = -2; col <= 2; col += 1) {
        if (Math.abs(row) + Math.abs(col) > 3) continue;
        block(row < 0 ? back : front, x + col * 4 * sx - 2, y + row * 4 * sy - 2, 4, 4, (row + col) % 2 ? spec.colors.petal_primary : spec.colors.petal_highlight);
      }
      break;
    case "lily":
      drawRadial(spec, back, front, x, y, true);
      block(front, x - 2, y - 2, 4, 4, spec.colors.flower_center);
      break;
    case "daisy":
      drawRadial(spec, back, front, x, y);
      break;
    case "lavender":
      for (let index = 0; index < 7; index += 1) {
        const offsetY = index * 3;
        const spread = 2 + index * 0.45;
        block(index < 3 ? back : front, x - spread - 2, y - 15 * sy + offsetY, 4, 3, spec.colors.petal_primary);
        block(index < 3 ? back : front, x + spread - 2, y - 15 * sy + offsetY, 4, 3, spec.colors.petal_highlight);
      }
      break;
    case "wildflower":
      drawRadial(spec, back, front, x - 5, y + 1, false);
      petal(front, x + 7, y - 4, 5, 5, spec.colors.petal_highlight);
      petal(front, x + 9, y + 2, 4, 4, spec.colors.petal_primary);
      break;
  }

  layers.bloom_back.addChild(back);
  layers.bloom_front.addChild(front);
}

export function drawFlowerTemplate(spec: FlowerRenderSpec, layers: Layers) {
  const { stemTop, bloomX } = drawStem(spec, layers);
  drawLeaves(spec, layers, stemTop);
  drawBloom(spec, layers, bloomX, stemTop - 2);
}

export const TEMPLATE_IDS: Record<FlowerSpecies, string> = {
  rose: "rose_v1", peony: "peony_v1", sunflower: "sunflower_v1",
  tulip: "tulip_v1", hydrangea: "hydrangea_v1", lily: "lily_v1",
  daisy: "daisy_v1", lavender: "lavender_v1", wildflower: "wildflower_v1",
};

import { Container, Graphics } from "pixi.js";

import { FLOWER_HEIGHT, FLOWER_WIDTH, drawFlowerTemplate } from "./templates";
import { RENDER_LAYER_ORDER, type FlowerRenderSpec, type RenderLayer } from "./types";
import { assertFlowerRenderSpec } from "./validate";

export interface PixelFlower {
  container: Container;
  bodyBounds: { x: number; y: number; width: number; height: number };
  update(elapsedMs: number): void;
  destroy(): void;
}

export function buildParticleLayout(seed: number | string, count = 12) {
  const particleSeed = Number(BigInt(seed) % 100000n);
  return Array.from({ length: count }, (_, index) => {
    const value = Math.sin(particleSeed * 0.013 + index * 17.17) * 43758.5453;
    const unit = value - Math.floor(value);
    const second = Math.sin(particleSeed * 0.021 + index * 9.73) * 24634.6345;
    return {
      x: 7 + unit * 34,
      y: 8 + (second - Math.floor(second)) * 38,
      delay: (unit + index / count) % 1,
    };
  });
}

function drawDecoration(spec: FlowerRenderSpec, target: Container) {
  if (spec.decoration === "none") return;
  const graphic = new Graphics();
  const color = spec.decoration === "dew_drops" ? "#BFE8F7" : spec.colors.particle;
  if (spec.decoration === "dew_drops") {
    graphic.rect(18, 31, 2, 3).fill(color).rect(29, 39, 2, 3).fill(color);
  } else if (spec.decoration === "leaf_sprigs") {
    graphic.rect(13, 35, 7, 2).fill(spec.colors.leaf).rect(28, 30, 7, 2).fill(spec.colors.leaf);
  } else if (spec.decoration === "star_charms") {
    graphic.rect(11, 18, 3, 3).fill(color).rect(35, 24, 2, 2).fill(color).rect(30, 10, 2, 2).fill(color);
  } else {
    graphic.rect(17, 42, 14, 2).fill(color).rect(15, 44, 5, 2).fill(color).rect(28, 44, 5, 2).fill(color);
  }
  target.addChild(graphic);
}

export function createPixelFlower(input: unknown): PixelFlower {
  assertFlowerRenderSpec(input);
  const spec = input;
  const root = new Container();
  root.label = `flower:${spec.species}`;

  const layers = Object.fromEntries(
    RENDER_LAYER_ORDER.map((name) => {
      const layer = new Container();
      layer.label = name;
      root.addChild(layer);
      return [name, layer];
    }),
  ) as Record<RenderLayer, Container>;

  const shadow = new Graphics().ellipse(24, 59, 12, 3).fill({ color: "#0D1711", alpha: 0.34 });
  layers.shadow.addChild(shadow);

  const bloom = drawFlowerTemplate(spec, layers);
  const { x, y, width, height } = root.getLocalBounds();
  drawDecoration(spec, layers.decoration);
  layers.decoration.children.forEach((detail) => { detail.y += bloom.y - 30; });

  const glow = new Graphics()
    .circle(bloom.x, bloom.y, Math.max(5, Math.round(spec.animation.glow_radius_ratio * 70)))
    .fill({ color: spec.colors.glow, alpha: spec.animation.glow_opacity * 0.25 });
  layers.glow.addChild(glow);

  const particleLayout = buildParticleLayout(spec.variation_seed);
  const particles = particleLayout.map((entry) => {
    const particle = new Graphics().rect(-1, -1, 2, 2).fill(spec.colors.particle);
    const y = entry.y + bloom.y - 22;
    particle.position.set(entry.x, y);
    layers.particles.addChild(particle);
    return { particle, ...entry, y };
  });
  layers.particles.visible = spec.animation.particle_rate > 0;

  const movingLayers = [layers.stem, layers.leaves, layers.bloom_back, layers.bloom_front, layers.decoration, layers.glow];
  for (const layer of movingLayers) {
    layer.pivot.set(FLOWER_WIDTH / 2, 58);
    layer.position.set(FLOWER_WIDTH / 2, 58);
  }

  const update = (elapsedMs: number) => {
    const cycle = elapsedMs / spec.animation.sway_period_ms + spec.animation.sway_phase;
    const sway = Math.sin(cycle * Math.PI * 2) * spec.animation.sway_amplitude;
    movingLayers.forEach((layer, index) => { layer.rotation = sway * (0.65 + index * 0.06); });
    layers.glow.alpha = 0.72 + Math.sin(cycle * Math.PI * 2) * 0.18;

    if (spec.animation.particle_rate > 0) {
      const particleCycle = elapsedMs * 0.00012 * spec.animation.particle_rate + spec.animation.particle_phase;
      particles.forEach(({ particle, x, y, delay }, index) => {
        const progress = (particleCycle + delay) % 1;
        particle.x = x + Math.sin(progress * Math.PI * 2 + index) * 2;
        particle.y = y - progress * 14;
        particle.alpha = Math.sin(progress * Math.PI);
      });
    }
  };

  return {
    container: root,
    bodyBounds: { x, y, width, height },
    update,
    destroy: () => root.destroy({ children: true }),
  };
}

export const FLOWER_STAGE_SIZE = { width: FLOWER_WIDTH, height: FLOWER_HEIGHT };

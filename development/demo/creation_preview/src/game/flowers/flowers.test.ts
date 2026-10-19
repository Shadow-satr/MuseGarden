import { describe, expect, it } from "vitest";

import previewGroups from "../../../public/flower-preview-specs.json";
import { buildParticleLayout } from "./renderer";
import { TEMPLATE_IDS } from "./templates";
import { RENDER_LAYER_ORDER } from "./types";
import { assertFlowerRenderSpec } from "./validate";

const validSpec = {
  renderer_schema_version: "1.0",
  template_id: "tulip_v1",
  species: "tulip",
  variation_seed: 42,
  colors: {
    petal_primary: "#D9A441", petal_secondary: "#9E6B2F",
    petal_highlight: "#F5D06F", flower_center: "#7A4F27",
    stem: "#47704B", leaf: "#5F8A58", glow: "#F7D77A", particle: "#FFE5A3",
  },
  geometry: {
    bloom_shape: "cup", leaf_shape: "lance", petal_count: 6,
    bloom_scale_x: 1, bloom_scale_y: 1, stem_height_ratio: 0.7,
    stem_curve: 0, leaf_count: 3, leaf_angle_offset: 0, anchor_x: 0.5, anchor_y: 1,
  },
  animation: {
    sway_amplitude: 0.04, sway_period_ms: 2400, sway_phase: 0.2,
    glow_opacity: 0.3, glow_radius_ratio: 0.1, particle_rate: 3.5, particle_phase: 0.4,
  },
  particle_effect: "sparkles",
  decoration: "dew_drops",
  growth_direction: "rising",
  layer_order: [...RENDER_LAYER_ORDER],
};

describe("Flower renderer contract", () => {
  it("accepts the v1 contract and all nine templates are registered", () => {
    expect(() => assertFlowerRenderSpec(validSpec)).not.toThrow();
    expect(Object.keys(TEMPLATE_IDS)).toHaveLength(9);
    for (const [species, template] of Object.entries(TEMPLATE_IDS)) {
      expect(template).toBe(`${species}_v1`);
    }
  });

  it("rejects incompatible versions, templates and layer order", () => {
    expect(() => assertFlowerRenderSpec({ ...validSpec, renderer_schema_version: "2.0" })).toThrow();
    expect(() => assertFlowerRenderSpec({ ...validSpec, template_id: "rose_v1" })).toThrow();
    expect(() => assertFlowerRenderSpec({ ...validSpec, layer_order: [...RENDER_LAYER_ORDER].reverse() })).toThrow();
  });

  it("builds deterministic particle layouts", () => {
    expect(buildParticleLayout(1234)).toEqual(buildParticleLayout(1234));
    expect(buildParticleLayout(1234)).not.toEqual(buildParticleLayout(1235));
    expect(buildParticleLayout(1234)).toHaveLength(12);
  });

  it("accepts exact 63-bit seed strings without losing identity", () => {
    const largeSeed = "603703287136832921";
    expect(() => assertFlowerRenderSpec({ ...validSpec, variation_seed: largeSeed })).not.toThrow();
    expect(() => assertFlowerRenderSpec({ ...validSpec, variation_seed: Number(largeSeed) })).toThrow();
    expect(() => assertFlowerRenderSpec({ ...validSpec, variation_seed: "9223372036854775808" })).toThrow();
    expect(() => assertFlowerRenderSpec({ ...validSpec, variation_seed: "01" })).toThrow();
    expect(buildParticleLayout(largeSeed)).toEqual(buildParticleLayout("603703287136832921"));
    expect(buildParticleLayout(largeSeed)).not.toEqual(buildParticleLayout("603703287136832922"));
  });

  it("accepts all 27 RenderSpecs exported by the Python Flower Engine", () => {
    expect(previewGroups).toHaveLength(9);
    for (const group of previewGroups) {
      expect(group.variants).toHaveLength(3);
      for (const spec of group.variants) {
        expect(() => assertFlowerRenderSpec(spec)).not.toThrow();
        expect(spec.species).toBe(group.species);
      }
      expect(new Set(group.variants.map((spec) => spec.variation_seed)).size).toBe(3);
    }
  });
});

import type { GardenPreviewPayload } from "./types";
import { assertGardenRenderSpec } from "./validate";

export interface PlantingClient {
  loadGarden(): Promise<GardenPreviewPayload>;
}

function assertPreviewPayload(value: unknown): asserts value is GardenPreviewPayload {
  if (!value || typeof value !== "object") throw new Error("花园响应必须是对象");
  const payload = value as Record<string, unknown>;
  assertGardenRenderSpec(payload.garden);
  if (!Array.isArray(payload.available_flowers)) throw new Error("可种植花朵列表无效");
  for (const flower of payload.available_flowers as Array<Record<string, unknown>>) {
    if (typeof flower.flower_artifact_id !== "string" ||
        typeof flower.template_id !== "string" ||
        typeof flower.species !== "string" ||
        typeof flower.scale !== "number") {
      throw new Error("可种植花朵无效");
    }
    assertGardenRenderSpec({
      ...(payload.garden as object),
      flowers: [{
        planting_record_id: "preview",
        flower_artifact_id: flower.flower_artifact_id,
        template_id: flower.template_id,
        grid_x: 0,
        grid_y: 0,
        pixel_x: 0,
        pixel_y: 0,
        scale: flower.scale,
        z_index: 0,
        render_spec: flower.render_spec,
      }],
    });
  }
}

async function readResponse(response: Response): Promise<GardenPreviewPayload> {
  const data: unknown = await response.json();
  if (!response.ok) {
    const message = data && typeof data === "object" && "error" in data
      ? String((data as { error: unknown }).error)
      : `HTTP ${response.status}`;
    throw new Error(message);
  }
  assertPreviewPayload(data);
  return data;
}

export const plantingClient: PlantingClient = {
  async loadGarden() {
    return readResponse(await fetch("/api/garden-preview"));
  },
};

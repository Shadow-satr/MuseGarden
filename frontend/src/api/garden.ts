import type { GardenRenderSpec } from "../rendering/flowers/types";
import { assertGardenRenderSpec } from "../rendering/flowers/validate";

export interface GardenLoadResult {
  spec: GardenRenderSpec;
  source: "live";
}

export async function loadGarden(signal?: AbortSignal): Promise<GardenLoadResult> {
  const response = signal
    ? await fetch("/api/garden-preview", { signal })
    : await fetch("/api/garden-preview");
  const payload: unknown = await response.json();
  if (!response.ok) {
    const message = payload && typeof payload === "object" && "error" in payload
      ? String(payload.error)
      : `HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!payload || typeof payload !== "object" || !("garden" in payload)) {
    throw new Error("花园响应缺少 GardenRenderSpec");
  }
  assertGardenRenderSpec(payload.garden);
  return { spec: payload.garden, source: "live" };
}

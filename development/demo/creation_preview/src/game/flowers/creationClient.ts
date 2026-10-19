import type { FlowerRenderSpec } from "./types";

export interface DemoCreation {
  creation_id: string;
  text: string;
  blueprint: { primary_emotion: string; scene: string };
  flower: { artifact_id: string; species: string; render_spec: FlowerRenderSpec } | null;
  music: { artifact_id: string; version: number; url: string };
  planting: { record_id: string; x: number; y: number } | null;
}

async function readJson<T>(response: Response): Promise<T> {
  const value = await response.json();
  if (!response.ok) throw new Error(value?.error || `HTTP ${response.status}`);
  return value as T;
}

export const creationClient = {
  async list(): Promise<DemoCreation[]> {
    const payload = await readJson<{ creations: DemoCreation[] }>(await fetch("/api/creations"));
    return payload.creations;
  },
  async create(text: string, gardenId: string, x: number, y: number): Promise<DemoCreation> {
    return readJson<DemoCreation>(await fetch("/api/creations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, garden_id: gardenId, x, y }),
    }));
  },
  async regenerate(creationId: string, modificationText: string): Promise<DemoCreation> {
    return readJson<DemoCreation>(await fetch(`/api/creations/${creationId}/music`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modification_text: modificationText }),
    }));
  },
  async digUp(gardenId: string, plantingId: string): Promise<void> {
    const response = await fetch(`/api/gardens/${gardenId}/plantings/${plantingId}`, {
      method: "DELETE",
    });
    await readJson(response);
  },
};

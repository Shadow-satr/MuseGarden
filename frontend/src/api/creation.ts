export interface CreationDraft {
  plantSpotId: string;
  text: string;
}

export interface CreationResult {
  creation_id: string;
  text: string;
  flower: { artifact_id: string; species: string; render_spec?: FlowerRenderSpec };
  planting: { record_id: string; x: number; y: number };
  music: { artifact_id: string; url: string; version?: number };
  latest_music_version?: number;
  music_versions?: MusicVersion[];
}

export interface MusicVersion {
  version_id: string;
  audio_artifact_id: string;
  version: number;
  modification_text: string | null;
  created_at: string;
  url: string;
  is_latest: boolean;
  is_selected: boolean;
}

export interface FlowerRenderSpec {
  species: string;
  colors: {
    petal_primary: string;
    petal_secondary: string;
    petal_highlight: string;
    flower_center: string;
    stem: string;
    leaf: string;
  };
  geometry: {
    bloom_shape: string;
    petal_count: number;
    bloom_scale_x: number;
    bloom_scale_y: number;
    stem_height_ratio: number;
    leaf_count: number;
  };
}

export interface FlowerMemory {
  creation_id: string;
  text: string;
  flower: { artifact_id: string; species: string; render_spec?: FlowerRenderSpec };
  planting: { record_id: string; x: number; y: number };
  music: { artifact_id: string; url: string; version?: number } | null;
  latest_music_version: number;
  music_versions: MusicVersion[];
}

export class CreationResponseError extends Error {}

export class FlowerMemoryNotFoundError extends Error {}

function isCreationResult(value: unknown): value is CreationResult {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  const flower = item.flower as Record<string, unknown> | null;
  const planting = item.planting as Record<string, unknown> | null;
  const music = item.music as Record<string, unknown> | null;
  const validRenderSpec = flower?.render_spec === undefined || (
    !!flower?.render_spec && typeof flower.render_spec === "object" &&
    (flower.render_spec as Record<string, unknown>).species === flower.species
  );
  return typeof item.creation_id === "string" && typeof item.text === "string" &&
    !!flower && typeof flower.artifact_id === "string" && typeof flower.species === "string" &&
    validRenderSpec &&
    !!planting && typeof planting.record_id === "string" &&
    typeof planting.x === "number" && typeof planting.y === "number" &&
    !!music && typeof music.artifact_id === "string" && typeof music.url === "string" &&
    /^\/api\/audio\/[0-9a-fA-F-]+$/.test(music.url);
}

function isFlowerMemory(value: unknown): value is FlowerMemory {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  const flower = item.flower as Record<string, unknown> | null;
  const planting = item.planting as Record<string, unknown> | null;
  const music = item.music as Record<string, unknown> | null | undefined;
  const validRenderSpec = flower?.render_spec === undefined || (
    !!flower?.render_spec && typeof flower.render_spec === "object" &&
    (flower.render_spec as Record<string, unknown>).species === flower.species
  );
  const validMusic = music == null || (
    typeof music.artifact_id === "string" && typeof music.url === "string" &&
    (/^\/api\/audio\/[0-9a-fA-F-]+$/.test(music.url) || music.url === "")
  );
  const versions = item.music_versions;
  const validVersions = Array.isArray(versions) && versions.every((version) => {
    if (!version || typeof version !== "object") return false;
    const candidate = version as Record<string, unknown>;
    return typeof candidate.version_id === "string" &&
      typeof candidate.audio_artifact_id === "string" &&
      typeof candidate.version === "number" && candidate.version >= 1 &&
      (candidate.modification_text === null || typeof candidate.modification_text === "string") &&
      typeof candidate.created_at === "string" && typeof candidate.url === "string" &&
      /^\/api\/audio\/[0-9a-fA-F-]+$/.test(candidate.url) &&
      typeof candidate.is_latest === "boolean" && typeof candidate.is_selected === "boolean";
  });
  return typeof item.creation_id === "string" && typeof item.text === "string" &&
    !!flower && typeof flower.artifact_id === "string" && typeof flower.species === "string" &&
    validRenderSpec &&
    !!planting && typeof planting.record_id === "string" &&
    typeof planting.x === "number" && typeof planting.y === "number" && validMusic &&
    typeof item.latest_music_version === "number" && validVersions;
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new Error(response.ok ? "后端响应无法读取" : `HTTP ${response.status}`);
  }
}

export async function loadFlowerMemory(
  plantingRecordId: string,
  flowerArtifactId: string,
  signal?: AbortSignal,
): Promise<FlowerMemory> {
  const response = await fetch("/api/creations", { signal });
  const payload = await readJson(response);
  if (!response.ok) {
    const message = payload && typeof payload === "object" && "error" in payload
      ? String(payload.error)
      : `HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!payload || typeof payload !== "object" || !("creations" in payload) || !Array.isArray(payload.creations)) {
    throw new Error("记忆列表格式无效");
  }
  const exact = payload.creations.find((item) => {
    if (!isFlowerMemory(item)) return false;
    return item.planting.record_id === plantingRecordId && item.flower.artifact_id === flowerArtifactId;
  });
  if (!exact) throw new FlowerMemoryNotFoundError("没有找到这朵花对应的记忆");
  return exact;
}

async function postFlowerMemory(path: string, body: object, signal?: AbortSignal): Promise<FlowerMemory> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  const payload = await readJson(response);
  if (!response.ok) {
    const message = payload && typeof payload === "object" && "error" in payload
      ? String(payload.error)
      : `HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!isFlowerMemory(payload)) throw new Error("音乐版本结果格式无效");
  return payload;
}

export function reviseFlowerMusic(
  creationId: string,
  modificationText: string,
  signal?: AbortSignal,
): Promise<FlowerMemory> {
  return postFlowerMemory(
    `/api/creations/${creationId}/music`,
    { modification_text: modificationText },
    signal,
  );
}

export function selectFlowerMusicVersion(
  creationId: string,
  audioArtifactId: string,
  signal?: AbortSignal,
): Promise<FlowerMemory> {
  return postFlowerMemory(
    `/api/creations/${creationId}/music-selection`,
    { audio_artifact_id: audioArtifactId },
    signal,
  );
}

export function spotCoordinates(plantSpotId: string): { x: number; y: number } {
  const match = /^spot:(\d+),(\d+)$/.exec(plantSpotId);
  if (!match) throw new Error("种植位置无效");
  return { x: Number(match[1]), y: Number(match[2]) };
}

export async function createMemory(
  gardenId: string,
  draft: CreationDraft,
  signal?: AbortSignal,
): Promise<CreationResult> {
  const { x, y } = spotCoordinates(draft.plantSpotId);
  const response = await fetch("/api/creations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ garden_id: gardenId, text: draft.text, x, y }),
    signal,
  });
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    if (response.ok) throw new CreationResponseError("后端已响应，但创作结果无法读取");
    throw new Error(`HTTP ${response.status}`);
  }
  if (!response.ok) {
    const message = payload && typeof payload === "object" && "error" in payload
      ? String(payload.error)
      : `HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!isCreationResult(payload) || payload.planting.x !== x || payload.planting.y !== y) {
    throw new CreationResponseError("创作结果不完整，请刷新花园后检查");
  }
  return payload as CreationResult;
}

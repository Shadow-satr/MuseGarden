import { afterEach, describe, expect, it, vi } from "vitest";

import { createMemory, loadFlowerMemory, removeFlowerFromGarden, reviseFlowerMusic, selectFlowerMusicVersion } from "./creation";

const result = {
  creation_id: "creation-1", text: "今天很开心",
  flower: { artifact_id: "flower-1", species: "tulip" },
  planting: { record_id: "planting-1", x: 8, y: 3 },
  music: { artifact_id: "audio-1", url: "/api/audio/12345678-1234-1234-1234-123456789abc" },
};
const memoryResult = {
  ...result,
  music: { ...result.music, version: 1 },
  latest_music_version: 1,
  music_versions: [{
    version_id: "revision-1", audio_artifact_id: "audio-1", version: 1,
    modification_text: null, created_at: "2026-10-19T10:00:00+08:00",
    url: result.music.url, is_latest: true, is_selected: true,
  }],
};

describe("creation API", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends the real backend schema and accepts the matching planting and audio", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => result,
    });
    vi.stubGlobal("fetch", fetchMock);
    const draft = { plantSpotId: "spot:8,3", text: "今天很开心" };
    expect(await createMemory("garden-1", draft)).toEqual(result);
    expect(fetchMock).toHaveBeenCalledWith("/api/creations", expect.objectContaining({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ garden_id: "garden-1", text: draft.text, x: 8, y: 3 }),
    }));
  });

  it("surfaces backend errors and rejects a result planted elsewhere", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 400, json: async () => ({ error: "位置已被占用" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...result, planting: { ...result.planting, x: 9 } }) });
    vi.stubGlobal("fetch", fetchMock);
    const draft = { plantSpotId: "spot:8,3", text: "今天很开心" };
    await expect(createMemory("garden-1", draft)).rejects.toThrow("位置已被占用");
    await expect(createMemory("garden-1", draft)).rejects.toThrow("创作结果不完整");
  });

  it("loads the memory that matches both the planting and flower ids", async () => {
    const other = {
      ...result,
      creation_id: "creation-2",
      text: "另一段记忆",
      planting: { record_id: "planting-2", x: 1, y: 1 },
      flower: { artifact_id: "flower-2", species: "rose" },
      music: { artifact_id: "audio-2", url: "/api/audio/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" },
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ creations: [{ ...other, latest_music_version: 1, music_versions: memoryResult.music_versions }, memoryResult] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    expect(await loadFlowerMemory("planting-1", "flower-1")).toEqual(memoryResult);
    expect(fetchMock).toHaveBeenCalledWith("/api/creations", { signal: undefined });
  });

  it("does not substitute another flower when the requested relation is absent", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ creations: [memoryResult] }),
    }));
    await expect(loadFlowerMemory("missing", "flower-1")).rejects.toThrow("没有找到这朵花对应的记忆");
  });

  it("still returns the persisted text when its audio is unavailable", async () => {
    const withoutAudio = { ...memoryResult, music: null };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ creations: [withoutAudio] }),
    }));
    expect(await loadFlowerMemory("planting-1", "flower-1")).toEqual(withoutAudio);
  });

  it("submits revision text and version selection to their stable creation", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => memoryResult })
      .mockResolvedValueOnce({ ok: true, json: async () => memoryResult });
    vi.stubGlobal("fetch", fetchMock);

    await expect(reviseFlowerMusic("creation-1", "更轻快一些")).resolves.toEqual(memoryResult);
    await expect(selectFlowerMusicVersion("creation-1", "audio-1")).resolves.toEqual(memoryResult);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/creations/creation-1/music", expect.objectContaining({
      method: "POST", body: JSON.stringify({ modification_text: "更轻快一些" }),
    }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/creations/creation-1/music-selection", expect.objectContaining({
      method: "POST", body: JSON.stringify({ audio_artifact_id: "audio-1" }),
    }));
  });

  it("removes a flower through its stable garden planting relation", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ garden: {} }) });
    vi.stubGlobal("fetch", fetchMock);

    await expect(removeFlowerFromGarden("garden-1", "planting-1")).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith("/api/gardens/garden-1/plantings/planting-1", {
      method: "DELETE", signal: undefined,
    });
  });
});

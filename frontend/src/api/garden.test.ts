import { afterEach, describe, expect, it, vi } from "vitest";

import { loadGarden } from "./garden";

vi.mock("../rendering/flowers/validate", () => ({ assertGardenRenderSpec: vi.fn() }));

describe("garden API", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads and validates the live GardenRenderSpec", async () => {
    const garden = { garden_id: "live-garden" };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ garden }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await loadGarden();
    expect(fetchMock).toHaveBeenCalledWith("/api/garden-preview");
    expect(result.spec).toBe(garden);
  });

  it("reports API failure instead of showing a static demo garden", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    await expect(loadGarden()).rejects.toThrow("offline");
  });
});

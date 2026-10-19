// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import gardenPreviewJson from "../public/garden-preview-spec.json";
import type { GardenPreviewPayload, GardenRenderSpec } from "./game/flowers/types";

const clientMocks = vi.hoisted(() => ({
  loadGarden: vi.fn(), list: vi.fn(), create: vi.fn(), regenerate: vi.fn(), digUp: vi.fn(),
}));

vi.mock("./game/flowers/plantingClient", () => ({ plantingClient: clientMocks }));
vi.mock("./game/flowers/creationClient", () => ({ creationClient: clientMocks }));
vi.mock("./game/flowers/GardenCanvas", () => ({
  GardenCanvas: ({ spec, highlight, onGridClick }: {
    spec: GardenRenderSpec;
    highlight?: { x: number; y: number } | null;
    onGridClick?: (cell: { x: number; y: number }) => void;
  }) => (
    <div data-testid="mock-garden" data-count={spec.flowers.length}
      data-highlight={highlight ? `${highlight.x},${highlight.y}` : "none"}>
      <button onClick={() => onGridClick?.({ x: 3, y: 3 })}>空地格子</button>
      <button onClick={() => onGridClick?.({ x: 11, y: 1 })}>已有花格子</button>
    </div>
  ),
}));

import App from "./App";

const garden = gardenPreviewJson as unknown as GardenRenderSpec;
const initialPayload: GardenPreviewPayload = { garden, available_flowers: [] };
const planted = garden.flowers.find((flower) => flower.grid_x === 11 && flower.grid_y === 1)!;
const creation = {
  creation_id: "creation-1",
  text: "比赛结束后松了一口气",
  blueprint: { primary_emotion: "满足感", scene: "比赛结束之后" },
  flower: { artifact_id: "flower-1", species: "tulip", render_spec: garden.flowers[0].render_spec },
  music: { artifact_id: "audio-v1", version: 1, url: "/api/audio/audio-v1" },
  planting: { record_id: "planting-1", x: 3, y: 3 },
};

describe("Garden creation and shovel interaction", () => {
  beforeEach(() => {
    clientMocks.loadGarden.mockReset().mockResolvedValue(initialPayload);
    clientMocks.list.mockReset().mockResolvedValue([]);
    clientMocks.create.mockReset();
    clientMocks.regenerate.mockReset();
    clientMocks.digUp.mockReset();
  });
  afterEach(cleanup);

  it("shows 1-based coordinates and creates from the selected empty cell", async () => {
    const user = userEvent.setup();
    const nextGarden = { ...garden, flowers: [
      ...garden.flowers,
      { ...garden.flowers[0], planting_record_id: "planting-1", flower_artifact_id: "flower-1", grid_x: 3, grid_y: 3 },
    ] };
    clientMocks.create.mockResolvedValue(creation);
    clientMocks.loadGarden.mockResolvedValueOnce(initialPayload)
      .mockResolvedValueOnce({ ...initialPayload, garden: nextGarden });
    clientMocks.regenerate.mockResolvedValue({
      ...creation, music: { artifact_id: "audio-v2", version: 2, url: "/api/audio/audio-v2" },
    });
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "空地格子" }));
    expect(screen.getByText(/已选择空地 \(4, 4\)/)).toBeTruthy();
    expect(screen.getByTestId("mock-garden").getAttribute("data-highlight")).toBe("3,3");
    expect(screen.queryByRole("button", { name: "种下一朵花" })).toBeNull();
    await user.type(screen.getByRole("textbox", { name: "记忆文字" }), creation.text);
    await user.click(screen.getByRole("button", { name: /生成记忆/ }));

    expect(await screen.findByLabelText("创作音乐")).toBeTruthy();
    expect(clientMocks.create).toHaveBeenCalledWith(creation.text, garden.garden_id, 3, 3);
    expect(screen.getByText(/新花已种在 \(4, 4\)/)).toBeTruthy();
    expect(screen.getByTestId("mock-garden").getAttribute("data-count")).toBe("10");
    await user.type(screen.getByRole("textbox", { name: "音乐修改要求" }), "更温暖一点");
    await user.click(screen.getByRole("button", { name: "修改音乐" }));
    await waitFor(() => expect(screen.getByLabelText("创作音乐").getAttribute("src")).toBe("/api/audio/audio-v2"));
    expect(screen.getByText("🌸 花已种在 (4, 4)")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "已有花格子" }));
    expect(screen.getByTestId("mock-garden").getAttribute("data-highlight")).toBe("11,1");
  });

  it("requires a second confirmation before permanently digging a planted flower", async () => {
    const user = userEvent.setup();
    clientMocks.digUp.mockResolvedValue(undefined);
    clientMocks.loadGarden.mockResolvedValueOnce(initialPayload)
      .mockResolvedValueOnce({ ...initialPayload, garden: {
        ...garden, flowers: garden.flowers.filter((flower) => flower.planting_record_id !== planted.planting_record_id),
      } });
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "已有花格子" }));
    expect(screen.queryByLabelText("创作记忆")).toBeNull();
    expect(screen.getByText(/向日葵 · \(12, 2\)/)).toBeTruthy();
    await user.click(screen.getByRole("button", { name: /铲除这朵花/ }));
    expect(screen.getByRole("dialog", { name: "确认永久铲除" })).toBeTruthy();
    expect(clientMocks.digUp).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "取消" }));
    expect(clientMocks.digUp).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: /铲除这朵花/ }));
    await user.click(screen.getByRole("button", { name: "确认永久铲除" }));
    await waitFor(() => expect(clientMocks.digUp).toHaveBeenCalledWith(garden.garden_id, planted.planting_record_id));
    expect(await screen.findByText(/已永久铲除 \(12, 2\)/)).toBeTruthy();
    expect(screen.getByTestId("mock-garden").getAttribute("data-count")).toBe("8");
    expect(screen.queryByText(/恢复/)).toBeNull();
  });

  it("keeps memory and music visible after its flower is removed", async () => {
    const user = userEvent.setup();
    const original = { ...creation, flower: { ...creation.flower, artifact_id: planted.flower_artifact_id },
      planting: { record_id: planted.planting_record_id, x: 11, y: 1 } };
    const archived = { ...original, flower: null, planting: null };
    clientMocks.list.mockResolvedValueOnce([original]).mockResolvedValueOnce([archived]);
    clientMocks.digUp.mockResolvedValue(undefined);
    clientMocks.loadGarden.mockResolvedValueOnce(initialPayload).mockResolvedValueOnce({
      ...initialPayload,
      garden: { ...garden, flowers: garden.flowers.filter((flower) => flower.planting_record_id !== planted.planting_record_id) },
    });
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "已有花格子" }));
    expect(await screen.findByLabelText("创作音乐")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: /铲除这朵花/ }));
    await user.click(screen.getByRole("button", { name: "确认永久铲除" }));
    expect(await screen.findByText("花已永久铲除 · 记忆保留")).toBeTruthy();
    expect(screen.getByLabelText("创作音乐").getAttribute("src")).toBe("/api/audio/audio-v1");
    expect(await screen.findByRole("region", { name: "保留的记忆" })).toBeTruthy();
  });

  it("shows a visible load error without mounting the garden", async () => {
    clientMocks.loadGarden.mockRejectedValue(new Error("offline"));
    render(<App />);
    expect(await screen.findByText(/花园数据加载失败/)).toBeTruthy();
    expect(screen.queryByTestId("mock-garden")).toBeNull();
  });
});

// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const world = vi.hoisted(() => ({
  init: vi.fn(), destroy: vi.fn(), setInputPaused: vi.fn(), refreshGarden: vi.fn(),
  playerWorldPosition: { x: 724, y: 543 },
  interact: null as null | ((target: unknown) => void),
}));
vi.mock("./world/GardenWorld", () => ({
  GardenWorld: class {
    init = world.init;
    destroy = world.destroy;
    setInputPaused = world.setInputPaused;
    refreshGarden = world.refreshGarden;
    currentGardenId = "garden-1";
    get playerWorldPosition() { return world.playerWorldPosition; }
    constructor(_host: HTMLElement, _onTargetChange: unknown, onInteract: (target: unknown) => void) {
      world.interact = onInteract;
    }
  },
}));
vi.mock("./api/creation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/creation")>()),
  createMemory: vi.fn(), loadFlowerMemory: vi.fn(), reviseFlowerMusic: vi.fn(), selectFlowerMusicVersion: vi.fn(),
}));

import App from "./App";
import { createMemory, CreationResponseError, loadFlowerMemory, reviseFlowerMusic, selectFlowerMusicVersion } from "./api/creation";

const createMock = vi.mocked(createMemory);
const loadFlowerMemoryMock = vi.mocked(loadFlowerMemory);
const reviseFlowerMusicMock = vi.mocked(reviseFlowerMusic);
const selectFlowerMusicVersionMock = vi.mocked(selectFlowerMusicVersion);
const result = {
  creation_id: "creation-1", text: "今天完成比赛",
  flower: { artifact_id: "flower-1", species: "tulip" },
  planting: { record_id: "planting-1", x: 4, y: 2 },
  music: { artifact_id: "audio-1", url: "/api/audio/12345678-1234-1234-1234-123456789abc" },
};
const memoryResult = {
  ...result,
  music: { ...result.music, version: 1 },
  latest_music_version: 1,
  music_versions: [{
    version_id: "revision-1", audio_artifact_id: "audio-1", version: 1,
    modification_text: null, created_at: "2026-10-19T10:00:00+08:00", url: result.music.url,
    is_latest: true, is_selected: true,
  }],
};
const flowerTarget = {
  kind: "flower", id: "flower:planting-1", x: 216, y: 120, gridX: 4, gridY: 2,
  cellSize: 48, plantingRecordId: "planting-1", flowerArtifactId: "flower-1", prompt: "查看记忆",
};

describe("Garden World shell", () => {
  afterEach(() => {
    cleanup();
    world.init.mockReset();
    world.destroy.mockReset();
    world.setInputPaused.mockReset();
    world.interact = null;
    createMock.mockReset();
    loadFlowerMemoryMock.mockReset();
    reviseFlowerMusicMock.mockReset();
    selectFlowerMusicVersionMock.mockReset();
    world.refreshGarden.mockReset();
  });

  it("mounts one world and keeps an HTML overlay above it", async () => {
    world.init.mockResolvedValue({ source: "live" });
    const user = userEvent.setup();
    const view = render(<App />);
    expect(screen.getByTestId("garden-world")).toBeTruthy();
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    await user.click(screen.getByRole("button", { name: "☰" }));
    expect(screen.getByRole("button", { name: "UI Layer ✓" })).toBeTruthy();
    expect(world.init).toHaveBeenCalledTimes(1);
    view.unmount();
    expect(world.destroy).toHaveBeenCalledTimes(1);
  });

  it("reports an error when the garden API is unavailable", async () => {
    world.init.mockRejectedValue(new Error("API unavailable"));
    render(<App />);
    await waitFor(() => expect(screen.getByText(/API unavailable/)).toBeTruthy());
    expect(world.destroy).toHaveBeenCalledTimes(1);
  });

  it("opens the map with M, pauses input, then closes with M or Escape", async () => {
    world.init.mockResolvedValue({ source: "live" });
    render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    fireEvent.keyDown(window, { key: "m" });
    expect(screen.getByRole("dialog", { name: "Garden Map" })).toBeTruthy();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(true);
    expect(screen.getByLabelText("完整花园地图与玩家位置").querySelector("circle")?.getAttribute("cx")).toBe("724");
    fireEvent.keyDown(window, { key: "m" });
    expect(screen.queryByRole("dialog", { name: "Garden Map" })).toBeNull();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(false);
    fireEvent.keyDown(window, { key: "m" });
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "Garden Map" })).toBeNull();
  });

  it("does not open the map while a creation panel or text input owns the keyboard", async () => {
    world.init.mockResolvedValue({ source: "live" });
    render(<App />);
    act(() => world.interact?.({ kind: "plant-spot", id: "spot:8,3", prompt: "种下记忆" }));
    fireEvent.keyDown(window, { key: "m" });
    expect(screen.queryByRole("dialog", { name: "Garden Map" })).toBeNull();
    fireEvent.keyDown(screen.getByRole("textbox", { name: "写下这段记忆" }), { key: "m" });
    expect(screen.queryByRole("dialog", { name: "Garden Map" })).toBeNull();
  });

  it("opens from a plant spot, pauses input, clears on cancel, and opens again", async () => {
    world.init.mockResolvedValue({ source: "live" });
    const user = userEvent.setup();
    render(<App />);
    const spot = { kind: "plant-spot", id: "spot:8,3", prompt: "种下记忆" };

    act(() => world.interact?.(spot));
    const dialog = screen.getByRole("dialog", { name: "留下一段记忆" });
    expect(dialog).toBeTruthy();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(true);
    const textarea = screen.getByRole("textbox", { name: "写下这段记忆" }) as HTMLTextAreaElement;
    expect(document.activeElement).toBe(textarea);
    expect((screen.getByRole("button", { name: "开始创作" }) as HTMLButtonElement).disabled).toBe(true);
    await user.type(textarea, "今天很开心");
    expect(textarea.value).toBe("今天很开心");
    expect(screen.getByText("5 / 500")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "取消" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(false);

    act(() => world.interact?.(spot));
    expect((screen.getByRole("textbox", { name: "写下这段记忆" }) as HTMLTextAreaElement).value).toBe("");
    expect(world.init).toHaveBeenCalledTimes(1);
  });

  it("opens the selected flower's persisted memory and restores movement on close", async () => {
    world.init.mockResolvedValue({ source: "live" });
    loadFlowerMemoryMock.mockResolvedValue(memoryResult);
    const user = userEvent.setup();
    render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());

    act(() => world.interact?.(flowerTarget));
    expect(screen.getByRole("dialog", { name: "这朵花的记忆" })).toBeTruthy();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(true);
    await waitFor(() => expect(screen.getByText("今天完成比赛")).toBeTruthy());
    expect(loadFlowerMemoryMock).toHaveBeenCalledWith("planting-1", "flower-1", expect.any(AbortSignal));
    expect(screen.getByRole("button", { name: "▶ 播放音乐" })).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "返回花园" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(false);
    expect(world.refreshGarden).not.toHaveBeenCalled();
  });

  it("keeps memories from two flowers separate", async () => {
    world.init.mockResolvedValue({ source: "live" });
    const second = {
      ...result, creation_id: "creation-2", text: "第二朵花的文字",
      flower: { artifact_id: "flower-2", species: "rose" },
      planting: { record_id: "planting-2", x: 5, y: 2 },
      music: { artifact_id: "audio-2", url: "/api/audio/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" },
    };
    const secondMemory = {
      ...second,
      music: { ...second.music, version: 1 },
      latest_music_version: 1,
      music_versions: [{ ...memoryResult.music_versions[0], version_id: "revision-2", audio_artifact_id: "audio-2", url: second.music.url }],
    };
    loadFlowerMemoryMock.mockResolvedValueOnce(memoryResult).mockResolvedValueOnce(secondMemory);
    const user = userEvent.setup();
    const view = render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    act(() => world.interact?.(flowerTarget));
    await waitFor(() => expect(screen.getByText("今天完成比赛")).toBeTruthy());
    await user.click(screen.getByRole("button", { name: "返回花园" }));
    act(() => world.interact?.({ ...flowerTarget, id: "flower:planting-2", plantingRecordId: "planting-2", flowerArtifactId: "flower-2" }));
    await waitFor(() => expect(screen.getByText("第二朵花的文字")).toBeTruthy());
    expect(screen.queryByText("今天完成比赛")).toBeNull();
    expect(view.container.querySelector("audio")?.getAttribute("src")).toBe(second.music.url);
  });

  it("revises the selected flower and persists history selection through the API", async () => {
    world.init.mockResolvedValue({ source: "live" });
    loadFlowerMemoryMock.mockResolvedValue(memoryResult);
    const v2 = {
      ...memoryResult,
      music: { artifact_id: "audio-2", version: 2, url: "/api/audio/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" },
      latest_music_version: 2,
      music_versions: [
        { ...memoryResult.music_versions[0], is_latest: false, is_selected: false },
        { version_id: "revision-2", audio_artifact_id: "audio-2", version: 2, modification_text: "更轻快", created_at: "2026-10-19T11:00:00+08:00", url: "/api/audio/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", is_latest: true, is_selected: true },
      ],
    };
    reviseFlowerMusicMock.mockResolvedValue(v2);
    selectFlowerMusicVersionMock.mockResolvedValue({
      ...v2,
      music: { ...memoryResult.music, version: 1 },
      music_versions: v2.music_versions.map((version) => ({ ...version, is_selected: version.version === 1 })),
    });
    const user = userEvent.setup();
    const view = render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    act(() => world.interact?.(flowerTarget));
    await waitFor(() => expect(screen.getByText("今天完成比赛")).toBeTruthy());
    await user.click(screen.getByRole("button", { name: "修改音乐" }));
    await user.type(screen.getByRole("textbox", { name: "修改要求" }), "更轻快");
    await user.click(screen.getByRole("button", { name: "生成新版音乐" }));
    await waitFor(() => expect(screen.getByText("V2")).toBeTruthy());
    expect(reviseFlowerMusicMock).toHaveBeenCalledWith("creation-1", "更轻快", expect.any(AbortSignal));
    expect(view.container.querySelector("audio")?.getAttribute("src")).toBe(v2.music.url);
    await user.click(screen.getAllByRole("button", { name: "选择 V1 音乐" })[0]);
    await waitFor(() => expect(selectFlowerMusicVersionMock).toHaveBeenCalledWith("creation-1", "audio-1", expect.any(AbortSignal)));
    expect(view.container.querySelector("audio")?.getAttribute("src")).toBe(memoryResult.music.url);
    expect(world.setInputPaused).toHaveBeenLastCalledWith(true);
  });

  it("sends the trimmed draft once, stays paused while loading, and shows the response", async () => {
    world.init.mockResolvedValue({ source: "live" });
    const user = userEvent.setup();
    let complete!: (value: typeof result) => void;
    createMock.mockReturnValue(new Promise((resolve) => { complete = resolve; }));
    world.refreshGarden.mockResolvedValue(undefined);
    render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    act(() => world.interact?.({ kind: "plant-spot", id: "spot:4,2", prompt: "种下记忆" }));
    const textarea = screen.getByRole("textbox", { name: "写下这段记忆" }) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "记".repeat(505) } });
    expect(textarea.value).toHaveLength(500);
    expect(screen.getByText("500 / 500")).toBeTruthy();
    fireEvent.change(textarea, { target: { value: "  今天完成比赛  " } });
    await user.click(screen.getByRole("button", { name: "开始创作" }));
    expect(createMock).toHaveBeenCalledWith("garden-1", { plantSpotId: "spot:4,2", text: "今天完成比赛" }, expect.any(AbortSignal));
    expect(createMock).toHaveBeenCalledTimes(1);
    expect(screen.getByText("正在创造你的记忆……")).toBeTruthy();
    expect((screen.getByRole("button", { name: "开始创作" }) as HTMLButtonElement).disabled).toBe(true);
    expect(world.setInputPaused).toHaveBeenLastCalledWith(true);
    act(() => complete(result));
    await waitFor(() => expect(screen.getByText("你的记忆已经种下了")).toBeTruthy());
    expect(world.refreshGarden).toHaveBeenCalledWith({ recordId: "planting-1", flowerArtifactId: "flower-1", x: 4, y: 2 }, expect.any(AbortSignal));
    expect(screen.getByText("今天完成比赛")).toBeTruthy();
    expect(screen.getByRole("button", { name: "▶ 播放音乐" })).toBeTruthy();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(true);
    await user.click(screen.getByRole("button", { name: "完成" }));
    expect(createMock).toHaveBeenCalledTimes(1);
    expect(world.setInputPaused).toHaveBeenLastCalledWith(false);
  });

  it("keeps the draft after failure, retries, and cancels an in-flight request", async () => {
    world.init.mockResolvedValue({ source: "live" });
    const user = userEvent.setup();
    createMock.mockRejectedValueOnce(new Error("暂时无法提交"));
    createMock.mockImplementationOnce(() => new Promise(() => {}));
    render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    act(() => world.interact?.({ kind: "plant-spot", id: "spot:8,3", prompt: "种下记忆" }));
    const textarea = screen.getByRole("textbox", { name: "写下这段记忆" }) as HTMLTextAreaElement;
    await user.type(textarea, "一段记忆");
    await user.click(screen.getByRole("button", { name: "开始创作" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("暂时无法提交"));
    expect(textarea.value).toBe("一段记忆");
    expect(world.setInputPaused).toHaveBeenLastCalledWith(true);
    await user.click(screen.getByRole("button", { name: "重新尝试" }));
    expect(createMock).toHaveBeenCalledTimes(2);
    expect(screen.getByText("正在创造你的记忆……")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "取消" }));
    const signal = createMock.mock.calls[1][2];
    expect(signal?.aborted).toBe(true);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(world.setInputPaused).toHaveBeenLastCalledWith(false);
  });

  it("retries only the garden refresh after creation already succeeded", async () => {
    world.init.mockResolvedValue({ source: "live" });
    createMock.mockResolvedValue(result);
    world.refreshGarden.mockRejectedValueOnce(new Error("花园暂时不可用"));
    world.refreshGarden.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    act(() => world.interact?.({ kind: "plant-spot", id: "spot:4,2", prompt: "种下记忆" }));
    await user.type(screen.getByRole("textbox", { name: "写下这段记忆" }), "今天完成比赛");
    await user.click(screen.getByRole("button", { name: "开始创作" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("花园暂时不可用"));
    expect(screen.queryByText("你的记忆已经种下了")).toBeNull();
    await user.click(screen.getByRole("button", { name: "重试刷新" }));
    await waitFor(() => expect(screen.getByText("你的记忆已经种下了")).toBeTruthy());
    expect(createMock).toHaveBeenCalledTimes(1);
    expect(world.refreshGarden).toHaveBeenCalledTimes(2);
  });

  it("does not offer a duplicate submission after an incomplete success response", async () => {
    world.init.mockResolvedValue({ source: "live" });
    createMock.mockRejectedValue(new CreationResponseError("创作结果不完整"));
    world.refreshGarden.mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<App />);
    await waitFor(() => expect(screen.getByText("花园已就绪")).toBeTruthy());
    act(() => world.interact?.({ kind: "plant-spot", id: "spot:4,2", prompt: "种下记忆" }));
    await user.type(screen.getByRole("textbox", { name: "写下这段记忆" }), "今天完成比赛");
    await user.click(screen.getByRole("button", { name: "开始创作" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("不要重复提交"));
    expect((screen.getByRole("button", { name: "开始创作" }) as HTMLButtonElement).disabled).toBe(true);
    expect(createMock).toHaveBeenCalledTimes(1);
  });
});

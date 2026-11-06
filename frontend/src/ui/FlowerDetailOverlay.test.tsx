// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FlowerDetailOverlay } from "./FlowerDetailOverlay";

const memory = {
  creation_id: "creation-1",
  text: "雨停后在河边散步",
  flower: {
    artifact_id: "flower-1", species: "lily", render_spec: {
      species: "lily",
      colors: { petal_primary: "#FFFFFF", petal_secondary: "#E5C6F2", petal_highlight: "#FFFFFF", flower_center: "#F3C95C", stem: "#4D7D4A", leaf: "#5B914C" },
      geometry: { bloom_shape: "trumpet", petal_count: 6, bloom_scale_x: 1, bloom_scale_y: 1, stem_height_ratio: 1, leaf_count: 2 },
    },
  },
  planting: { record_id: "planting-1", x: 3, y: 4 },
  music: { artifact_id: "audio-1", url: "/api/audio/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" },
  latest_music_version: 1,
  music_versions: [{
    version_id: "revision-1", audio_artifact_id: "audio-1", version: 1,
    modification_text: null, created_at: "2026-10-19T10:00:00+08:00",
    url: "/api/audio/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", is_latest: true, is_selected: true,
  }],
};

const props = {
  revisionStatus: "idle" as const,
  revisionError: "",
  selectingAudioId: null,
  onClose: () => {},
  onRetry: () => {},
  onRevise: async () => true,
  onSelectVersion: async () => {},
};

describe("FlowerDetailOverlay", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("shows the persisted text and its own audio URL", () => {
    const view = render(<FlowerDetailOverlay status="success" memory={memory} error="" {...props} />);
    expect(screen.getByRole("dialog", { name: "这朵花的记忆" })).toBeTruthy();
    expect(screen.getByText("雨停后在河边散步")).toBeTruthy();
    expect(screen.getByText("百合")).toBeTruthy();
    expect(screen.getByRole("img", { name: "百合 花朵图案" })).toBeTruthy();
    expect(view.container.querySelector("audio")?.getAttribute("src")).toBe(memory.music.url);
  });

  it("keeps close and retry available when loading fails", () => {
    const retry = vi.fn();
    const close = vi.fn();
    render(<FlowerDetailOverlay status="error" memory={null} error="记忆不存在" {...props} onClose={close} onRetry={retry} />);
    screen.getByRole("button", { name: "重新读取" }).click();
    screen.getByRole("button", { name: "返回花园" }).click();
    expect(screen.getByRole("alert").textContent).toContain("记忆不存在");
    expect(retry).toHaveBeenCalledOnce();
    expect(close).toHaveBeenCalledOnce();
  });

  it("keeps the memory readable when no audio URL is available", () => {
    render(<FlowerDetailOverlay status="success" memory={{ ...memory, music: null }} error="" {...props} />);
    expect(screen.getByText("雨停后在河边散步")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("没有可播放的音乐");
    expect(screen.queryByRole("button", { name: "▶ 播放音乐" })).toBeNull();
  });

  it("accepts longer music instructions and keeps the original memory", async () => {
    const revise = vi.fn().mockResolvedValue(true);
    const user = userEvent.setup();
    render(<FlowerDetailOverlay status="success" memory={memory} error="" {...props} onRevise={revise} />);
    await user.click(screen.getByRole("button", { name: "修改音乐" }));
    const input = screen.getByRole("textbox", { name: "修改要求" }) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "轻".repeat(510) } });
    expect(input.value).toHaveLength(510);
    expect(screen.queryByText(/\/ 10000/)).toBeNull();
    fireEvent.change(input, { target: { value: "  更轻快，保留钢琴  " } });
    await user.click(screen.getByRole("button", { name: "生成新版音乐" }));
    await waitFor(() => expect(revise).toHaveBeenCalledWith("更轻快，保留钢琴"));
    expect(screen.getByText("雨停后在河边散步")).toBeTruthy();
  });

  it("shows real history and selects a different version", async () => {
    const select = vi.fn().mockResolvedValue(undefined);
    const v2 = {
      ...memory.music_versions[0], version_id: "revision-2", audio_artifact_id: "audio-2",
      version: 2, modification_text: "更温柔", url: "/api/audio/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      is_latest: true, is_selected: false,
    };
    const history = { ...memory, latest_music_version: 2, music_versions: [{ ...memory.music_versions[0], is_latest: false }, v2] };
    const user = userEvent.setup();
    const view = render(<FlowerDetailOverlay status="success" memory={history} error="" {...props} onSelectVersion={select} />);
    expect(screen.getByRole("button", { name: "修改 V1 的名称" }).textContent).toBe("初始版本");
    expect(screen.getByText("更温柔")).toBeTruthy();
    const instruction = screen.getByRole("button", { name: "展开 V2 修改要求" });
    await user.click(instruction);
    expect(instruction.textContent).toBe("更温柔");
    expect(view.container.querySelector(".music-version-full-instruction")?.textContent).toBe("更温柔");
    await user.click(screen.getAllByRole("button", { name: "选择 V2 音乐" })[0]);
    expect(select).toHaveBeenCalledWith("audio-2");
  });

  it("saves a version name with Enter and abandons it with Escape", async () => {
    const rename = vi.fn().mockResolvedValue(true);
    const user = userEvent.setup();
    render(<FlowerDetailOverlay status="success" memory={memory} error="" {...props} onRenameVersion={rename} />);
    await user.click(screen.getByRole("button", { name: "修改 V1 的名称" }));
    const input = screen.getByRole("textbox", { name: "V1 版本名称" });
    await user.clear(input);
    await user.type(input, "晨光版{Enter}");
    await waitFor(() => expect(rename).toHaveBeenCalledWith("audio-1", "晨光版"));

    await user.click(screen.getByRole("button", { name: "修改 V1 的名称" }));
    const secondInput = screen.getByRole("textbox", { name: "V1 版本名称" });
    await user.clear(secondInput);
    await user.type(secondInput, "不会保存{Escape}");
    expect(screen.queryByRole("textbox", { name: "V1 版本名称" })).toBeNull();
    expect(rename).toHaveBeenCalledTimes(1);
  });
});

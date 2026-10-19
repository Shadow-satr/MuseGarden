// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AudioPlayer } from "./AudioPlayer";

describe("creation result audio", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("plays and pauses the returned audio URL", async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
    const pause = vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
    const view = render(<AudioPlayer url="/api/audio/12345678-1234-1234-1234-123456789abc" />);
    expect(view.container.querySelector("audio")?.getAttribute("src")).toBe("/api/audio/12345678-1234-1234-1234-123456789abc");
    fireEvent.click(screen.getByRole("button", { name: "▶ 播放音乐" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "⏸ 暂停音乐" })).toBeTruthy());
    expect(play).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "⏸ 暂停音乐" }));
    expect(pause).toHaveBeenCalled();
    view.unmount();
  });
});

// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { WorldOverlay } from "./WorldOverlay";
import type { Interactable } from "../world/interactions";

const spot: Interactable = { kind: "plant-spot", id: "spot", x: 0, y: 0, gridX: 0, gridY: 0, cellSize: 48, prompt: "种下记忆" };
const flower: Interactable = { kind: "flower", id: "flower", x: 0, y: 0, gridX: 0, gridY: 0, cellSize: 48, plantingRecordId: "planting", flowerArtifactId: "artifact", prompt: "查看记忆" };

describe("WorldOverlay interaction hint", () => {
  afterEach(cleanup);

  it("follows the current target and hides when none is nearby", () => {
    const view = render(<WorldOverlay target={null} interactionMessage="" />);
    expect(screen.queryByText("种下记忆")).toBeNull();
    view.rerender(<WorldOverlay target={spot} interactionMessage="" />);
    expect(screen.getByText(/种下记忆/).textContent).toContain("E");
    view.rerender(<WorldOverlay target={flower} interactionMessage="已选择花朵" />);
    expect(screen.getByText(/查看记忆/)).toBeTruthy();
    expect(screen.getByText("已选择花朵")).toBeTruthy();
    view.rerender(<WorldOverlay target={null} interactionMessage="" />);
    expect(screen.queryByText(/查看记忆/)).toBeNull();
  });
});

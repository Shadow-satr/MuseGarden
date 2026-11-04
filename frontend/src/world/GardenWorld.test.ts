// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";

const appState = vi.hoisted(() => ({ current: null as unknown }));
vi.mock("../api/garden", () => ({ loadGarden: vi.fn() }));
vi.mock("pixi.js", () => {
  class Container {
    label = "";
    x = 0;
    y = 0;
    children: Container[] = [];
    position = { set: (x: number, y: number) => { this.x = x; this.y = y; } };
    addChild(...children: Container[]) { this.children.push(...children); }
    removeChild(child: Container) { this.children = this.children.filter((item) => item !== child); }
    destroy() { this.children = []; }
  }
  class Graphics extends Container {
    rect() { return this; }
    fill() { return this; }
    stroke() { return this; }
    clear() { return this; }
  }
  class Rectangle {
    constructor(public x: number, public y: number, public width: number, public height: number) {}
  }
  class Texture {
    static EMPTY = new Texture({ frame: new Rectangle(0, 0, 1, 1) });
    source = { width: 1254, height: 1254 };
    width: number;
    height: number;
    constructor(options: { frame: Rectangle }) {
      this.width = options.frame.width;
      this.height = options.frame.height;
    }
  }
  class Sprite extends Container {
    anchor = { set: () => {} };
    width = 0;
    height = 0;
    constructor(public texture: Texture) { super(); }
  }
  const Assets = { load: async () => new Texture({ frame: new Rectangle(0, 0, 1254, 1254) }) };
  class Application {
    canvas = document.createElement("canvas");
    renderer = {};
    stage = new Container();
    tick: ((ticker: { deltaMS: number }) => void) | null = null;
    ticker = {
      add: (tick: (ticker: { deltaMS: number }) => void) => { this.tick = tick; },
      remove: (tick: (ticker: { deltaMS: number }) => void) => {
        if (this.tick === tick) this.tick = null;
      },
    };
    destroyed = false;
    async init() { appState.current = this; }
    destroy() { this.destroyed = true; }
    step(deltaMS: number) { this.tick?.({ deltaMS }); }
  }
  return { Application, Assets, Container, Graphics, Rectangle, Sprite, Texture };
});
vi.mock("./WorldScene", async () => {
  const { Container } = await import("pixi.js");
  return {
    gardenViewportSize: (value: typeof spec) => ({ width: value.pixel_width + 72, height: value.pixel_height + 72 }),
    mapWorldContentSize: () => ({ width: spec.pixel_width * 2, height: spec.pixel_height * 2 }),
    WorldScene: class {
    container = new Container();
    entities = new Container();
    constructor() { this.container.addChild(this.entities); }
    setPlayerCell() {}
    setCameraTarget() {}
    update() {}
    destroy() { this.container.destroy(); }
  } };
});

import { GardenWorld } from "./GardenWorld";
import { loadGarden } from "../api/garden";

interface TestApplication {
  stage: { children: Array<{ children: Array<{ children: Array<{ x: number; y: number; label: string }> }> }> };
  destroyed: boolean;
  step(deltaMS: number): void;
}

const spec = { garden_id: "garden-1", pixel_width: 768, pixel_height: 480, grid_width: 16, grid_height: 10, cell_size: 48, flowers: [] };

describe("GardenWorld keyboard integration", () => {
  it("attaches a player, handles WASD and arrows, then removes listeners", async () => {
    const host = document.createElement("div");
    const world = new GardenWorld(host);
    world.loadGarden = vi.fn().mockResolvedValue({ spec, source: "live" });
    await world.init();

    const app = appState.current as TestApplication;
    const player = app.stage.children[0].children[0].children[0];
    expect(host.querySelector("canvas")).toBeTruthy();
    expect(host.style.aspectRatio).toBe("840 / 552");
    expect(player.label).toBe("player");

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    app.step(50);
    app.step(50);
    expect(player.y).toBeCloseTo(372);
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "w" }));
    app.step(50);
    expect(player.y).toBeCloseTo(372);

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
    app.step(100);
    expect(player.x).toBeCloseTo(460);
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowRight" }));

    for (const [key, dx, dy] of [
      ["a", -12, 0], ["s", 0, 12], ["d", 12, 0],
      ["ArrowUp", 0, -12], ["ArrowLeft", -12, 0], ["ArrowDown", 0, 12],
    ] as const) {
      const beforeX = player.x;
      const beforeY = player.y;
      window.dispatchEvent(new KeyboardEvent("keydown", { key }));
      app.step(100);
      window.dispatchEvent(new KeyboardEvent("keyup", { key }));
      expect(player.x - beforeX).toBeCloseTo(dx);
      expect(player.y - beforeY).toBeCloseTo(dy);
    }

    world.destroy();
    expect(app.destroyed).toBe(true);
    expect(host.childElementCount).toBe(0);
    expect(host.style.aspectRatio).toBe("");
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "d" }));
    app.step(100);
    expect(player.x).toBeCloseTo(448);
  });

  it("updates the target after movement and invokes it once on E", async () => {
    const onTargetChange = vi.fn();
    const onInteract = vi.fn();
    const world = new GardenWorld(document.createElement("div"), onTargetChange, onInteract);
    world.loadGarden = vi.fn().mockResolvedValue({ spec, source: "live" });
    await world.init();
    const app = appState.current as TestApplication;
    expect(onTargetChange).toHaveBeenLastCalledWith(expect.objectContaining({ id: "spot:28,24" }));

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    for (let i = 0; i < 6; i += 1) app.step(100);
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "w" }));
    expect(onTargetChange).toHaveBeenLastCalledWith(expect.objectContaining({ id: "spot:28,19" }));

    const openingKey = new KeyboardEvent("keydown", { key: "e", cancelable: true });
    window.dispatchEvent(openingKey);
    expect(openingKey.defaultPrevented).toBe(true);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "e", repeat: true }));
    expect(onInteract).toHaveBeenCalledTimes(1);
    expect(onInteract).toHaveBeenCalledWith(expect.objectContaining({ prompt: "种下记忆" }));

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "s" }));
    for (let i = 0; i < 6; i += 1) app.step(100);
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "s" }));
    expect(onTargetChange).toHaveBeenLastCalledWith(expect.objectContaining({ id: "spot:28,24" }));
    world.destroy();
  });

  it("pauses movement and E while the creation overlay is open, then resumes", async () => {
    const onInteract = vi.fn();
    const world = new GardenWorld(document.createElement("div"), vi.fn(), onInteract);
    world.loadGarden = vi.fn().mockResolvedValue({ spec, source: "live" });
    await world.init();
    const app = appState.current as TestApplication;
    const player = app.stage.children[0].children[0].children[0];

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    for (let i = 0; i < 6; i += 1) app.step(100);
    expect(player.y).toBeCloseTo(312);
    world.setInputPaused(true);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "e" }));
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "d" }));
    app.step(100);
    expect(player.x).toBeCloseTo(448);
    expect(player.y).toBeCloseTo(312);
    expect(onInteract).not.toHaveBeenCalled();

    world.setInputPaused(false);
    app.step(100);
    expect(player.x).toBeCloseTo(448);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "d" }));
    app.step(100);
    expect(player.x).toBeCloseTo(460);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "e" }));
    expect(onInteract).toHaveBeenCalledTimes(1);
    world.destroy();
  });

  it("refreshes the planted flower at the chosen spot without moving the player", async () => {
    const onTargetChange = vi.fn();
    const world = new GardenWorld(document.createElement("div"), onTargetChange);
    world.loadGarden = vi.fn().mockResolvedValue({ spec, source: "live" });
    await world.init();
    const app = appState.current as TestApplication;
    const player = app.stage.children[0].children[0].children[0];
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    for (let i = 0; i < 6; i += 1) app.step(100);
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "w" }));
    expect(onTargetChange).toHaveBeenLastCalledWith(expect.objectContaining({ id: "spot:28,19" }));
    world.setInputPaused(true);
    const flower = {
      planting_record_id: "planting-1", flower_artifact_id: "flower-1",
      grid_x: 28, grid_y: 19, pixel_x: 456, pixel_y: 312,
      placement_schema_version: "terrain-v1", flower_size: "small",
      occupied_tiles: [[28, 19]],
    };
    vi.mocked(loadGarden).mockResolvedValue({ spec: { ...spec, flowers: [flower] } as never, source: "live" });
    await expect(world.refreshGarden({ recordId: "planting-1", flowerArtifactId: "flower-1", x: 29, y: 19 }))
      .rejects.toThrow("新花尚未出现在选中的空地");
    expect(onTargetChange).toHaveBeenLastCalledWith(expect.objectContaining({ id: "spot:28,19" }));
    await world.refreshGarden({ recordId: "planting-1", flowerArtifactId: "flower-1", x: 28, y: 19 });
    const refreshedPlayer = app.stage.children[0].children[0].children[0];
    expect(refreshedPlayer).toBe(player);
    expect(refreshedPlayer.x).toBe(448);
    expect(refreshedPlayer.y).toBe(312);
    expect(onTargetChange).toHaveBeenLastCalledWith(expect.objectContaining({ id: "flower:planting-1" }));
    expect(world.currentGardenId).toBe("garden-1");
    world.destroy();
  });

  it("uses Delete or Backspace only for a flower currently under the player's feet", async () => {
    const onDeleteFlower = vi.fn();
    const world = new GardenWorld(document.createElement("div"), vi.fn(), vi.fn(), onDeleteFlower);
    world.loadGarden = vi.fn().mockResolvedValue({ spec, source: "live" });
    await world.init();
    const flower = {
      planting_record_id: "planting-1", flower_artifact_id: "flower-1",
      grid_x: 28, grid_y: 24, pixel_x: 456, pixel_y: 392,
      placement_schema_version: "terrain-v1", flower_size: "small",
      occupied_tiles: [[28, 24]],
    };
    vi.mocked(loadGarden).mockResolvedValue({ spec: { ...spec, flowers: [flower] } as never, source: "live" });
    await world.refreshGarden();

    const deletionKey = new KeyboardEvent("keydown", { key: "Delete", cancelable: true });
    window.dispatchEvent(deletionKey);
    expect(deletionKey.defaultPrevented).toBe(true);
    expect(onDeleteFlower).toHaveBeenCalledWith(expect.objectContaining({ id: "flower:planting-1" }));
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Delete", repeat: true }));
    expect(onDeleteFlower).toHaveBeenCalledTimes(1);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Backspace" }));
    expect(onDeleteFlower).toHaveBeenCalledTimes(2);
    world.destroy();
  });
});

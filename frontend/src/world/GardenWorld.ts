import { Application, type Texture } from "pixi.js";

import { loadGarden, type GardenLoadResult } from "../api/garden";
import type { GardenRenderSpec } from "../rendering/flowers/types";
import { gardenViewportSize, mapWorldContentSize, WorldScene } from "./WorldScene";
import { loadMapArtTexture } from "./MapArt";
import { loadPlayerAnimations, Player, type PlayerAnimations } from "./entities/Player";
import { createInteractables, InteractionManager, type Interactable } from "./interactions";

const MOVEMENT_KEYS = new Set(["w", "a", "s", "d", "arrowup", "arrowleft", "arrowdown", "arrowright"]);

/** React owns the host element; this class owns everything inside the Pixi world. */
export class GardenWorld {
  private app: Application | null = null;
  private scene: WorldScene | null = null;
  private player: Player | null = null;
  private mapTexture: Texture | null = null;
  private gardenId: string | null = null;
  private interactions: InteractionManager | null = null;
  private disposed = false;
  private inputPaused = false;
  private elapsedMs = 0;
  private readonly heldKeys = new Set<string>();

  constructor(
    private readonly host: HTMLElement,
    private readonly onTargetChange: (target: Interactable | null) => void = () => {},
    private readonly onInteract: (target: Interactable) => void = () => {},
  ) {}

  async init(): Promise<GardenLoadResult | null> {
    const result = await this.loadGarden();
    if (this.disposed) return null;

    const app = new Application();
    this.app = app;
    const viewport = gardenViewportSize(result.spec);
    try {
      await app.init({
        width: viewport.width,
        height: viewport.height,
        backgroundAlpha: 0,
        antialias: false,
        resolution: 1,
      });
    } catch (error) {
      if (app.renderer) app.destroy(true);
      if (this.app === app) this.app = null;
      throw error;
    }
    if (this.disposed) {
      app.destroy(true);
      this.app = null;
      return null;
    }

    const [playerAnimations, mapTexture] = await Promise.all([loadPlayerAnimations(), loadMapArtTexture()]);
    if (this.disposed) return null;
    this.mapTexture = mapTexture;

    app.canvas.className = "world-canvas";
    app.canvas.setAttribute("aria-label", "MuseGarden 花园世界");
    this.host.style.aspectRatio = `${viewport.width} / ${viewport.height}`;
    this.host.replaceChildren(app.canvas);
    this.render(result.spec, playerAnimations);
    app.ticker.add(this.tick);
    window.addEventListener("keydown", this.onKeyDown);
    window.addEventListener("keyup", this.onKeyUp);
    window.addEventListener("blur", this.clearKeys);
    return result;
  }

  loadGarden(): Promise<GardenLoadResult> {
    return loadGarden();
  }

  get currentGardenId(): string | null {
    return this.gardenId;
  }

  async refreshGarden(
    expected?: { recordId: string; flowerArtifactId: string; x: number; y: number },
    signal?: AbortSignal,
  ): Promise<void> {
    const result = await loadGarden(signal);
    if (signal?.aborted || this.disposed) return;
    const spec = result.spec;
    if (spec.garden_id !== this.gardenId) throw new Error("刷新返回了另一座花园");
    if (expected && !spec.flowers.some((flower) =>
      flower.planting_record_id === expected.recordId &&
      flower.flower_artifact_id === expected.flowerArtifactId &&
      flower.grid_x === expected.x && flower.grid_y === expected.y,
    )) throw new Error("新花尚未出现在选中的空地，请重试刷新");
    if (!this.app || !this.scene || !this.player) throw new Error("花园尚未就绪");

    const targets = createInteractables(spec);
    if (!this.mapTexture) throw new Error("地图资源尚未就绪");
    const next = new WorldScene(spec, this.mapTexture);
    const old = this.scene;
    old.entities.removeChild(this.player.container);
    next.setPlayerCell(this.player.container.x, this.player.container.y);
    next.entities.addChild(this.player.container);
    next.setCameraTarget(this.player.container.x, this.player.container.y);
    this.app.stage.removeChild(old.container);
    this.app.stage.addChild(next.container);
    old.destroy();
    this.scene = next;
    this.interactions = new InteractionManager(targets, this.onInteract);
    this.onTargetChange(this.interactions.update(this.player.container.x, this.player.container.y));
  }

  setInputPaused(paused: boolean): void {
    this.inputPaused = paused;
    if (paused) this.clearKeys();
  }

  render(spec: GardenRenderSpec, playerAnimations: PlayerAnimations): void {
    if (this.disposed || !this.app) return;
    const targets = createInteractables(spec);
    if (!this.mapTexture) return;
    const next = new WorldScene(spec, this.mapTexture);
    const worldSize = mapWorldContentSize();
    // The current creation grid begins in the upper-left garden field of the
    // supplied map; Step 13 will assign each painted field its stable IDs.
    const player = new Player(worldSize.width, worldSize.height, spec.cell_size, playerAnimations, {
      x: spec.pixel_width / 2,
      y: spec.pixel_height / 2,
    });
    next.setPlayerCell(player.container.x, player.container.y);
    next.entities.addChild(player.container);
    next.setCameraTarget(player.container.x, player.container.y);
    const interactions = new InteractionManager(targets, this.onInteract);
    interactions.update(player.container.x, player.container.y);
    if (this.scene) {
      this.app.stage.removeChild(this.scene.container);
      this.scene.destroy();
    }
    this.scene = next;
    this.gardenId = spec.garden_id;
    this.player = player;
    this.interactions = interactions;
    this.onTargetChange(interactions.currentTarget);
    this.elapsedMs = 0;
    this.app.stage.addChild(next.container);
  }

  private readonly tick = (ticker: { deltaMS: number }) => {
    this.elapsedMs += ticker.deltaMS;
    this.scene?.update(this.elapsedMs);
    if (this.player) {
      this.player.setMovement(
        this.inputPaused ? 0 : Number(this.heldKeys.has("d") || this.heldKeys.has("arrowright")) -
          Number(this.heldKeys.has("a") || this.heldKeys.has("arrowleft")),
        this.inputPaused ? 0 : Number(this.heldKeys.has("s") || this.heldKeys.has("arrowdown")) -
          Number(this.heldKeys.has("w") || this.heldKeys.has("arrowup")),
      );
      this.player.update(ticker.deltaMS);
      this.scene?.setPlayerCell(this.player.container.x, this.player.container.y);
      this.scene?.setCameraTarget(this.player.container.x, this.player.container.y);
      const before = this.interactions?.currentTarget?.id;
      const target = this.interactions?.update(this.player.container.x, this.player.container.y) ?? null;
      if (before !== target?.id) this.onTargetChange(target);
    }
  };

  private readonly onKeyDown = (event: KeyboardEvent) => {
    const key = event.key.toLowerCase();
    if (this.inputPaused) return;
    if (key === "e" && !event.repeat && !event.altKey && !event.ctrlKey && !event.metaKey) {
      if (!(event.target instanceof HTMLElement && event.target.closest("input, textarea, [contenteditable='true']"))) {
        if (this.interactions?.currentTarget) {
          event.preventDefault();
          this.interactions.interact();
        }
      }
      return;
    }
    if (!MOVEMENT_KEYS.has(key) || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.target instanceof HTMLElement && event.target.closest("input, textarea, [contenteditable='true']")) return;
    this.heldKeys.add(key);
    if (key.startsWith("arrow")) event.preventDefault();
  };

  private readonly onKeyUp = (event: KeyboardEvent) => {
    this.heldKeys.delete(event.key.toLowerCase());
  };

  private readonly clearKeys = () => {
    this.heldKeys.clear();
  };

  destroy(): void {
    if (this.disposed) return;
    this.disposed = true;
    window.removeEventListener("keydown", this.onKeyDown);
    window.removeEventListener("keyup", this.onKeyUp);
    window.removeEventListener("blur", this.clearKeys);
    this.clearKeys();
    if (this.app) {
      this.app.ticker.remove(this.tick);
      if (this.scene) {
        this.app.stage.removeChild(this.scene.container);
        this.scene.destroy();
      }
      if (this.app.renderer) this.app.destroy(true);
    }
    this.scene = null;
    this.gardenId = null;
    this.player = null;
    this.interactions = null;
    this.app = null;
    this.mapTexture = null;
    this.host.replaceChildren();
    this.host.style.removeProperty("aspect-ratio");
    this.onTargetChange(null);
  }
}

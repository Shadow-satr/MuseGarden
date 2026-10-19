import { Assets, Container, Rectangle, Sprite, Texture } from "pixi.js";

import sheetData from "../../assets/player-walk-sheet.json";

export type Facing = "front" | "left" | "right" | "back";

interface PlayerSheetMeta {
  frameWidth: number;
  frameHeight: number;
  characterHeight: number;
  baseline: number;
  columns: number;
  rows: Record<Facing, number>;
  idleColumn: number;
  walkColumns: number[];
  /** Index into `walk`, not a sheet column. */
  startIndex: Record<Facing, number>;
}

export interface PlayerAnimation {
  idle: Texture;
  walk: Texture[];
  startIndex: number;
}

export type PlayerAnimations = Record<Facing, PlayerAnimation>;

const PLAYER_HEIGHT = 58;
const SPEED_PX_PER_SECOND = 120;
const WALK_FPS = 9;
const MAX_DELTA_MS = 100;
const PLAYER_SHEET_URL = new URL("../../assets/player-walk-sheet.png", import.meta.url).href;

const SHEET = sheetData as PlayerSheetMeta;

export async function loadPlayerAnimations(): Promise<PlayerAnimations> {
  const sheet = await Assets.load<Texture>(PLAYER_SHEET_URL);
  const frame = (column: number, row: number) =>
    new Texture({
      source: sheet.source,
      frame: new Rectangle(
        column * SHEET.frameWidth,
        row * SHEET.frameHeight,
        SHEET.frameWidth,
        SHEET.frameHeight,
      ),
    });

  const animations = {} as PlayerAnimations;
  for (const facing of Object.keys(SHEET.rows) as Facing[]) {
    const row = SHEET.rows[facing];
    animations[facing] = {
      idle: frame(SHEET.idleColumn, row),
      walk: SHEET.walkColumns.map((column) => frame(column, row)),
      startIndex: SHEET.startIndex[facing] % SHEET.walkColumns.length,
    };
  }
  return animations;
}

/** The container's position is the character's feet in world coordinates. */
export class Player {
  readonly container = new Container();
  readonly speed = SPEED_PX_PER_SECOND;
  facing: Facing = "front";
  private readonly sprite: Sprite;
  private movementX = 0;
  private movementY = 0;
  private moving = false;
  private walkFrame = 0;
  private walkElapsedMs = 0;

  constructor(
    private readonly worldWidth: number,
    private readonly worldHeight: number,
    private readonly cellSize: number,
    private readonly animations: PlayerAnimations,
  ) {
    this.container.label = "player";
    this.sprite = new Sprite(animations.front.idle);
    this.sprite.anchor.set(0.5, SHEET.baseline / SHEET.frameHeight);
    this.setVisualSize();
    this.container.addChild(this.sprite);
    this.container.position.set(worldWidth / 2, worldHeight / 2);
    this.clampToWorld();
  }

  setMovement(x: number, y: number): void {
    const length = Math.hypot(x, y);
    this.movementX = length > 1 ? x / length : x;
    this.movementY = length > 1 ? y / length : y;
    if (x === 0 && y === 0) {
      if (this.moving) {
        this.moving = false;
        this.walkElapsedMs = 0;
        this.sprite.texture = this.animations[this.facing].idle;
        this.setVisualSize();
      }
      return;
    }

    const facing: Facing = Math.abs(y) >= Math.abs(x)
      ? (y < 0 ? "back" : "front")
      : (x < 0 ? "left" : "right");
    const turned = facing !== this.facing;
    if (turned) this.facing = facing;

    if (!this.moving) {
      this.moving = true;
      this.walkFrame = this.animations[facing].startIndex;
      this.walkElapsedMs = 0;
      this.showWalkFrame();
    } else if (turned) {
      // Keep the step phase when changing direction; only swap the sprite row.
      this.showWalkFrame();
    }
  }

  private showWalkFrame(): void {
    const animation = this.animations[this.facing];
    this.walkFrame %= animation.walk.length;
    this.sprite.texture = animation.walk[this.walkFrame];
    this.setVisualSize();
  }

  private setVisualSize(): void {
    // Every cell uses the same canvas and character-to-canvas ratio, so the
    // visible character keeps exactly PLAYER_HEIGHT pixels in every frame.
    this.sprite.height = PLAYER_HEIGHT * SHEET.frameHeight / SHEET.characterHeight;
    this.sprite.width = this.sprite.height * this.sprite.texture.width / this.sprite.texture.height;
  }

  update(deltaMs: number): void {
    if (!Number.isFinite(deltaMs) || deltaMs <= 0) return;
    const elapsed = Math.min(deltaMs, MAX_DELTA_MS);

    if (this.moving) {
      this.walkElapsedMs += elapsed;
      const frameMs = 1000 / WALK_FPS;
      while (this.walkElapsedMs >= frameMs) {
        this.walkElapsedMs -= frameMs;
        this.walkFrame += 1;
        this.showWalkFrame();
      }
    }

    const distance = this.speed * elapsed / 1000;
    this.container.x += this.movementX * distance;
    this.container.y += this.movementY * distance;
    this.clampToWorld();
  }

  private clampToWorld(): void {
    // The logical position is the player's feet. Keep those feet on the
    // centre line of the outermost cells so every garden row is reachable.
    const edgeInset = this.cellSize / 2;
    this.container.x = Math.max(edgeInset, Math.min(this.worldWidth - edgeInset, this.container.x));
    this.container.y = Math.max(edgeInset, Math.min(this.worldHeight - edgeInset, this.container.y));
  }
}

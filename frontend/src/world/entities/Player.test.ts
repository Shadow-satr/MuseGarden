import { describe, expect, it } from "vitest";
import { Sprite, Texture } from "pixi.js";

import { Player, type PlayerAnimations } from "./Player";

function texture(): Texture {
  return new Texture({ source: Texture.WHITE.source });
}

function animation(startIndex = 0) {
  return {
    idle: texture(),
    walk: Array.from({ length: 6 }, () => texture()),
    startIndex,
  };
}

function animations(): PlayerAnimations {
  return {
    front: animation(1),
    left: animation(4),
    right: animation(1),
    back: animation(1),
  };
}

describe("Player movement", () => {
  it("starts in the garden and moves continuously at a fixed speed", () => {
    const frames = animations();
    const player = new Player(768, 480, 48, frames);
    expect([player.container.x, player.container.y]).toEqual([384, 240]);
    expect(player.container.label).toBe("player");
    expect(player.container.children).toHaveLength(1);
    const sprite = player.container.children[0] as Sprite;
    expect(sprite.texture).toBe(frames.front.idle);
    expect(sprite.anchor.x).toBe(0.5);
    expect(sprite.anchor.y).toBeCloseTo(376 / 384);
    expect(sprite.height).toBeCloseTo(58 * 384 / 352);

    player.setMovement(1, 0);
    for (let i = 0; i < 10; i += 1) player.update(50);
    expect(player.container.x).toBeCloseTo(444);
    expect(player.container.y).toBe(240);
  });

  it("normalizes diagonal movement", () => {
    const straight = new Player(768, 480, 48, animations());
    const diagonal = new Player(768, 480, 48, animations());
    straight.setMovement(1, 0);
    diagonal.setMovement(1, -1);
    straight.update(100);
    diagonal.update(100);
    const straightDistance = straight.container.x - 384;
    const diagonalDistance = Math.hypot(diagonal.container.x - 384, diagonal.container.y - 240);
    expect(diagonalDistance).toBeCloseTo(straightDistance);
  });

  it("keeps the player's feet inside every outermost grid cell", () => {
    const player = new Player(768, 480, 48, animations());
    player.setMovement(-1, -1);
    for (let i = 0; i < 1000; i += 1) player.update(100);
    expect(player.container.x).toBe(24);
    expect(player.container.y).toBe(24);
    expect(Math.floor(player.container.x / 48)).toBe(0);
    expect(Math.floor(player.container.y / 48)).toBe(0);
    player.setMovement(1, 1);
    for (let i = 0; i < 1000; i += 1) player.update(100);
    expect(player.container.x).toBe(744);
    expect(player.container.y).toBe(456);
    expect(Math.floor(player.container.x / 48)).toBe(15);
    expect(Math.floor(player.container.y / 48)).toBe(9);
  });

  it("starts each direction on its neutral walk frame and idles when stopped", () => {
    const frames = animations();
    for (const [x, y, facing, start] of [
      [0, -1, "back", 1], [0, 1, "front", 1], [-1, 0, "left", 4], [1, 0, "right", 1],
    ] as const) {
      const player = new Player(768, 480, 48, frames);
      const sprite = player.container.children[0] as Sprite;
      player.setMovement(x, y);
      expect(player.facing).toBe(facing);
      expect(sprite.texture).toBe(frames[facing].walk[start]);
      player.setMovement(0, 0);
      expect(sprite.texture).toBe(frames[facing].idle);
    }
  });

  it("advances walk frames at about nine per second and loops", () => {
    const frames = animations();
    const player = new Player(768, 480, 48, frames);
    const sprite = player.container.children[0] as Sprite;
    player.setMovement(1, 0);
    expect(sprite.texture).toBe(frames.right.walk[1]);

    // 100ms x 2 crosses the 111ms frame interval, so the next frame is due.
    player.update(100);
    expect(sprite.texture).toBe(frames.right.walk[1]);
    player.update(100);
    expect(sprite.texture).toBe(frames.right.walk[2]);

    for (let i = 0; i < 10; i += 1) player.update(100);
    expect(sprite.texture).toBe(frames.right.walk[5]);

    player.setMovement(0, 0);
    expect(sprite.texture).toBe(frames.right.idle);
  });

  it("keeps the step phase when only the facing changes mid-walk", () => {
    const frames = animations();
    const player = new Player(768, 480, 48, frames);
    const sprite = player.container.children[0] as Sprite;
    player.setMovement(1, 0);
    player.update(100);
    player.update(100);
    expect(sprite.texture).toBe(frames.right.walk[2]);

    player.setMovement(0, -1);
    expect(player.facing).toBe("back");
    expect(sprite.texture).toBe(frames.back.walk[2]);

    player.setMovement(0, 0);
    expect(sprite.texture).toBe(frames.back.idle);
  });
});

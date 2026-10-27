import type { GardenRenderSpec } from "../rendering/flowers/types";
import {
  flowerOccupiedTiles,
  flowerWorldPosition,
} from "./GardenMapLayout";
import { MUSE_GARDEN_TERRAIN, TERRAIN_CELL_SIZE } from "./TerrainMap";

export type Interactable =
  | { kind: "plant-spot"; id: string; x: number; y: number; gridX: number; gridY: number; cellSize: number; prompt: "种下记忆" }
  | { kind: "flower"; id: string; x: number; y: number; gridX: number; gridY: number; cellSize: number; plantingRecordId: string; flowerArtifactId: string; prompt: "查看记忆" };

export function createInteractables(spec: GardenRenderSpec): Interactable[] {
  const occupied = new Set(
    spec.flowers.flatMap((flower) => flowerOccupiedTiles(flower).map(([x, y]) => `${x},${y}`)),
  );
  const spots: Interactable[] = [...MUSE_GARDEN_TERRAIN.entries()]
    .filter(({ terrain }) => terrain === "SOIL")
    .filter(({ column, row }) => !occupied.has(`${column},${row}`))
    .map(({ column: gridX, row: gridY }) => ({
      kind: "plant-spot",
      id: `spot:${gridX},${gridY}`,
      x: (gridX + 0.5) * TERRAIN_CELL_SIZE,
      y: (gridY + 0.5) * TERRAIN_CELL_SIZE,
      gridX,
      gridY,
      cellSize: TERRAIN_CELL_SIZE,
      prompt: "种下记忆",
    }));
  const flowers: Interactable[] = spec.flowers.map((flower) => {
    const world = flowerWorldPosition(flower);
    const size = flower.flower_size === "large" ? TERRAIN_CELL_SIZE * 3 : TERRAIN_CELL_SIZE;
    return {
      kind: "flower",
      id: `flower:${flower.planting_record_id}`,
      x: world.x,
      y: world.y,
      gridX: flower.grid_x,
      gridY: flower.grid_y,
      cellSize: size,
      plantingRecordId: flower.planting_record_id,
      flowerArtifactId: flower.flower_artifact_id,
      prompt: "查看记忆",
    };
  });
  return [...spots, ...flowers];
}

export class InteractionManager {
  currentTarget: Interactable | null = null;

  constructor(
    private readonly targets: readonly Interactable[],
    private readonly onInteract: (target: Interactable) => void,
  ) {}

  update(playerX: number, playerY: number): Interactable | null {
    // Player.container is anchored at the feet. Both spots and flowers become
    // interactive only while those feet are inside their grid cell.
    let closest: Interactable | null = null;
    let closestDistance = Infinity;
    for (const target of this.targets) {
      const halfSize = target.cellSize / 2;
      if (playerX < target.x - halfSize || playerX >= target.x + halfSize ||
          playerY < target.y - halfSize || playerY >= target.y + halfSize) continue;
      const distance = (target.x - playerX) ** 2 + (target.y - playerY) ** 2;
      if (distance <= closestDistance) {
        closest = target;
        closestDistance = distance;
      }
    }
    this.currentTarget = closest;
    return closest;
  }

  interact(): void {
    if (this.currentTarget) this.onInteract(this.currentTarget);
  }
}

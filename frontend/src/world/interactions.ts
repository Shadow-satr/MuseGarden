import type { GardenRenderSpec } from "../rendering/flowers/types";

export type Interactable =
  | { kind: "plant-spot"; id: string; x: number; y: number; gridX: number; gridY: number; cellSize: number; prompt: "种下记忆" }
  | { kind: "flower"; id: string; x: number; y: number; gridX: number; gridY: number; cellSize: number; plantingRecordId: string; flowerArtifactId: string; prompt: "查看记忆" };

export function createInteractables(spec: GardenRenderSpec): Interactable[] {
  const occupied = new Set(spec.flowers.map((flower) => `${flower.grid_x},${flower.grid_y}`));
  const spots: Interactable[] = [];
  for (let gridY = 0; gridY < spec.grid_height; gridY += 1) {
    for (let gridX = 0; gridX < spec.grid_width; gridX += 1) {
      if (occupied.has(`${gridX},${gridY}`)) continue;
      spots.push({
        kind: "plant-spot",
        id: `spot:${gridX},${gridY}`,
        x: (gridX + 0.5) * spec.cell_size,
        y: (gridY + 0.5) * spec.cell_size,
        gridX,
        gridY,
        cellSize: spec.cell_size,
        prompt: "种下记忆",
      });
    }
  }
  const flowers: Interactable[] = spec.flowers.map((flower) => ({
    kind: "flower",
    id: `flower:${flower.planting_record_id}`,
    x: flower.pixel_x,
    y: flower.pixel_y,
    gridX: flower.grid_x,
    gridY: flower.grid_y,
    cellSize: spec.cell_size,
    plantingRecordId: flower.planting_record_id,
    flowerArtifactId: flower.flower_artifact_id,
    prompt: "查看记忆",
  }));
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
      if (Math.floor(playerX / target.cellSize) !== target.gridX ||
          Math.floor(playerY / target.cellSize) !== target.gridY) continue;
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

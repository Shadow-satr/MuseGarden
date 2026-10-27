import { TERRAIN_COLORS } from "../world/TerrainColors";
import { MUSE_GARDEN_TERRAIN, type TerrainType } from "../world/TerrainMap";

const LABELS: Array<[TerrainType, string]> = [
  ["GRASS", "草地"],
  ["WATER", "水域"],
  ["PATH", "道路"],
  ["SOIL", "种植位"],
  ["STRUCTURE", "建筑"],
  ["BRIDGE", "桥梁"],
];

export function MapOverview() {
  return <main className="map-overview-page">
    <svg
      className="map-overview-canvas"
      viewBox={`0 0 ${MUSE_GARDEN_TERRAIN.width} ${MUSE_GARDEN_TERRAIN.height}`}
      role="img"
      aria-label="MuseGarden 完整格子地图"
    >
      {[...MUSE_GARDEN_TERRAIN.entries()].map(({ column, row, terrain }) => <rect
        key={`${column}:${row}`}
        x={column * MUSE_GARDEN_TERRAIN.cellSize}
        y={row * MUSE_GARDEN_TERRAIN.cellSize}
        width={Math.min(MUSE_GARDEN_TERRAIN.cellSize, MUSE_GARDEN_TERRAIN.width - column * MUSE_GARDEN_TERRAIN.cellSize)}
        height={Math.min(MUSE_GARDEN_TERRAIN.cellSize, MUSE_GARDEN_TERRAIN.height - row * MUSE_GARDEN_TERRAIN.cellSize)}
        fill={TERRAIN_COLORS[terrain]}
      />)}
    </svg>
    <aside className="map-overview-legend" aria-label="地图图例">
      <strong>GRID MAP V1</strong>
      {LABELS.map(([terrain, label]) => <span key={terrain}>
        <i style={{ backgroundColor: TERRAIN_COLORS[terrain] }} />{label}
      </span>)}
    </aside>
  </main>;
}


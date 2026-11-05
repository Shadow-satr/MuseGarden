import { TERRAIN_COLORS } from "../world/TerrainColors";
import { MUSE_GARDEN_TERRAIN, type TerrainType } from "../world/TerrainMap";

interface MiniMapOverlayProps {
  playerPosition: { x: number; y: number } | null;
}

/** A read-only map view. Terrain always comes from the same source as the Pixi world. */
export function MiniMapOverlay({ playerPosition }: MiniMapOverlayProps) {
  const width = MUSE_GARDEN_TERRAIN.width;
  const height = MUSE_GARDEN_TERRAIN.height;
  const x = Math.max(0, Math.min(width, playerPosition?.x ?? 0));
  const y = Math.max(0, Math.min(height, playerPosition?.y ?? 0));
  return <div className="mini-map-backdrop" role="presentation">
    <section className="mini-map-panel" role="dialog" aria-modal="true" aria-label="Garden Map">
      <header className="mini-map-header">
        <div><p className="mini-map-eyebrow">MUSEGARDEN · EXPLORATION</p><h2>花园地图 <small>Garden Map</small></h2></div>
        <span className="mini-map-hint"><kbd>M</kbd> / <kbd>Esc</kbd> 关闭</span>
      </header>
      <svg className="mini-map-canvas" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="完整花园地图与玩家位置">
        {[...MUSE_GARDEN_TERRAIN.entries()].map(({ column, row, terrain }) => <rect
          key={`${column}:${row}`} x={column * MUSE_GARDEN_TERRAIN.cellSize} y={row * MUSE_GARDEN_TERRAIN.cellSize}
          width={Math.min(MUSE_GARDEN_TERRAIN.cellSize, width - column * MUSE_GARDEN_TERRAIN.cellSize)}
          height={Math.min(MUSE_GARDEN_TERRAIN.cellSize, height - row * MUSE_GARDEN_TERRAIN.cellSize)}
          fill={TERRAIN_COLORS[terrain as TerrainType]}
        />)}
        <circle className="mini-map-player" cx={x} cy={y} r={18} />
      </svg>
      <div className="mini-map-footer" aria-label="地图图例">
        <span><i style={{ backgroundColor: "#f4e477" }} />当前位置</span>
        <span><i style={{ backgroundColor: TERRAIN_COLORS.SOIL }} />种植区域</span>
        <span><i style={{ backgroundColor: TERRAIN_COLORS.PATH }} />道路</span>
        <span><i style={{ backgroundColor: TERRAIN_COLORS.WATER }} />水域</span>
      </div>
    </section>
  </div>;
}



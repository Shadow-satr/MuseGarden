import type { FlowerRenderSpec } from "../api/creation";

interface FlowerPortraitProps {
  species: string;
  renderSpec?: FlowerRenderSpec;
}

function radialPetals(spec: FlowerRenderSpec) {
  const count = Math.min(12, Math.max(5, spec.geometry.petal_count));
  const rx = 9 * spec.geometry.bloom_scale_x;
  const ry = 7 * spec.geometry.bloom_scale_y;
  return Array.from({ length: count }, (_, index) => {
    const angle = (360 / count) * index;
    return <ellipse
      key={index}
      cx="36"
      cy={36 - ry}
      rx={Math.max(3, rx * 0.46)}
      ry={Math.max(4, ry * 0.82)}
      fill={index % 3 === 0 ? spec.colors.petal_highlight : spec.colors.petal_primary}
      transform={`rotate(${angle} 36 36)`}
    />;
  });
}

function bloom(spec: FlowerRenderSpec) {
  const { bloom_shape: shape } = spec.geometry;
  if (shape === "spike_cluster") {
    return Array.from({ length: 5 }, (_, index) => <rect key={index} x={30 + (index % 2) * 7} y={13 + index * 6} width="7" height="7" fill={index % 2 ? spec.colors.petal_secondary : spec.colors.petal_primary} />);
  }
  if (shape === "trumpet") {
    return <><path d="M25 22 L47 22 L43 43 L29 43 Z" fill={spec.colors.petal_primary} /><path d="M29 23 L43 23 L40 29 L32 29 Z" fill={spec.colors.petal_highlight} /></>;
  }
  if (shape === "clustered_sphere" || shape === "open_cluster") {
    return <>{[[28, 31], [38, 27], [44, 36], [34, 42], [25, 40]].map(([cx, cy], index) => <circle key={index} cx={cx} cy={cy} r={index === 1 ? 10 : 8} fill={index % 2 ? spec.colors.petal_primary : spec.colors.petal_secondary} />)}<circle cx="36" cy="35" r="4" fill={spec.colors.flower_center} /></>;
  }
  if (shape === "cup") {
    return <><path d="M24 27 Q36 48 48 27 Q36 20 24 27 Z" fill={spec.colors.petal_primary} /><path d="M28 28 Q36 39 44 28" fill="none" stroke={spec.colors.petal_highlight} strokeWidth="3" /></>;
  }
  return <>{radialPetals(spec)}<circle cx="36" cy="36" r="6" fill={spec.colors.flower_center} /><circle cx="36" cy="36" r="2" fill={spec.colors.petal_secondary} /></>;
}

/** A compact detail view made from the same persisted Flower Engine render spec as the garden. */
export function FlowerPortrait({ species, renderSpec }: FlowerPortraitProps) {
  if (!renderSpec) return null;
  const stemTop = 54 - 18 * renderSpec.geometry.stem_height_ratio;
  return <svg className="flower-detail-portrait" viewBox="0 0 72 64" role="img" aria-label={`${species} 花朵图案`} shapeRendering="crispEdges">
    <path d={`M36 57 L36 ${stemTop}`} stroke={renderSpec.colors.stem} strokeWidth="3" />
    {Array.from({ length: Math.min(4, Math.max(0, renderSpec.geometry.leaf_count)) }, (_, index) => {
      const side = index % 2 ? 1 : -1;
      const y = 49 - index * 7;
      return <path key={index} d={`M36 ${y} Q${36 + side * 12} ${y - 7} ${36 + side * 15} ${y + 1} Q${36 + side * 6} ${y + 3} 36 ${y}`} fill={renderSpec.colors.leaf} />;
    })}
    <g transform={`translate(0 ${stemTop - 30})`}>{bloom(renderSpec)}</g>
  </svg>;
}

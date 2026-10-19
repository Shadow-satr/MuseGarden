import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { GardenWorld } from "../world/GardenWorld";
import type { Interactable } from "../world/interactions";

interface GardenWorldViewProps {
  onTargetChange: (target: Interactable | null) => void;
  onInteract: (target: Interactable) => void;
  paused: boolean;
  onReady?: (world: GardenWorld | null) => void;
}

export function GardenWorldView({ onTargetChange, onInteract, paused, onReady }: GardenWorldViewProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const worldRef = useRef<GardenWorld | null>(null);
  const [status, setStatus] = useState("正在进入花园…");

  useEffect(() => {
    if (!hostRef.current) return;
    const world = new GardenWorld(hostRef.current, onTargetChange, onInteract);
    worldRef.current = world;
    let active = true;
    void world.init().then((result) => {
      if (active && result) {
        setStatus("花园已就绪");
        onReady?.(world);
      }
    }).catch((error) => {
      if (active) {
        world.destroy();
        setStatus(`花园渲染失败：${String(error)}`);
      }
    });
    return () => {
      active = false;
      world.destroy();
      worldRef.current = null;
      onReady?.(null);
    };
  }, [onTargetChange, onInteract, onReady]);

  useLayoutEffect(() => {
    worldRef.current?.setInputPaused(paused);
  }, [paused]);

  return <div className="world-container">
    <div className="world-host" ref={hostRef} aria-label="花园场景" data-testid="garden-world" />
    <span className="world-status" role="status">{status}</span>
  </div>;
}

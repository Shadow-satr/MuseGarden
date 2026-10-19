import { useEffect, useRef, type MouseEvent } from "react";
import { Application } from "pixi.js";

import { createGardenScene } from "./gardenRenderer";
import type { GardenGridCell, GardenRenderSpec } from "./types";

interface GardenCanvasProps {
  spec: GardenRenderSpec;
  highlight?: GardenGridCell | null;
  onGridClick?: (cell: GardenGridCell) => void;
}

export function GardenCanvas({ spec, highlight = null, onGridClick }: GardenCanvasProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<ReturnType<typeof createGardenScene> | undefined>(undefined);
  const highlightRef = useRef(highlight);
  highlightRef.current = highlight;

  useEffect(() => {
    let disposed = false;
    let initialized = false;
    let destroyed = false;
    let app: Application | undefined;
    let scene: ReturnType<typeof createGardenScene> | undefined;

    const destroy = () => {
      if (!initialized || destroyed) return;
      destroyed = true;
      sceneRef.current = undefined;
      scene?.destroy();
      app?.destroy(true);
    };

    const mount = async () => {
      app = new Application();
      try {
        await app.init({
          width: spec.pixel_width,
          height: spec.pixel_height,
          backgroundAlpha: 0,
          antialias: false,
          resolution: 1,
        });
        initialized = true;
        if (disposed || !hostRef.current) {
          destroy();
          return;
        }

        app.canvas.className = "garden-canvas";
        app.canvas.setAttribute("aria-label", "MuseGarden pixel garden preview");
        hostRef.current.replaceChildren(app.canvas);
        scene = createGardenScene(spec);
        sceneRef.current = scene;
        app.stage.addChild(scene.container);
        scene.setHighlight(highlightRef.current);

        let elapsedMs = 0;
        app.ticker.add((ticker) => {
          elapsedMs += ticker.deltaMS;
          scene?.update(elapsedMs);
        });
      } catch (error) {
        if (disposed) return;
        console.error("无法初始化像素花园", error);
        hostRef.current?.replaceChildren(document.createTextNode("花园渲染失败"));
      }
    };

    void mount();
    return () => {
      disposed = true;
      destroy();
    };
  }, [spec]);

  useEffect(() => {
    sceneRef.current?.setHighlight(highlight);
  }, [highlight, spec]);

  const eventToCell = (event: MouseEvent<HTMLDivElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const pixelX = (event.clientX - bounds.left) * spec.pixel_width / bounds.width;
    const pixelY = (event.clientY - bounds.top) * spec.pixel_height / bounds.height;
    return {
      x: Math.max(0, Math.min(spec.grid_width - 1, Math.floor(pixelX / spec.cell_size))),
      y: Math.max(0, Math.min(spec.grid_height - 1, Math.floor(pixelY / spec.cell_size))),
    };
  };

  return (
    <div
      ref={hostRef}
      className={`garden-canvas-host${onGridClick ? " is-interactive" : ""}`}
      data-testid="garden-canvas"
      onClick={(event) => onGridClick?.(eventToCell(event))}
    />
  );
}

import { useEffect, useRef } from "react";
import { Application } from "pixi.js";

import { createPixelFlower, FLOWER_STAGE_SIZE } from "./renderer";
import type { FlowerRenderSpec } from "./types";

interface FlowerCanvasProps {
  spec: FlowerRenderSpec;
  paused: boolean;
}

export function FlowerCanvas({ spec, paused }: FlowerCanvasProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

  useEffect(() => {
    let disposed = false;
    let initialized = false;
    let destroyed = false;
    let app: Application | undefined;
    let flower: ReturnType<typeof createPixelFlower> | undefined;

    const destroy = () => {
      if (!initialized || destroyed) return;
      destroyed = true;
      flower?.destroy();
      app?.destroy(true);
    };

    const mount = async () => {
      app = new Application();
      try {
        await app.init({
          width: FLOWER_STAGE_SIZE.width * 3,
          height: FLOWER_STAGE_SIZE.height * 3,
          backgroundAlpha: 0,
          antialias: false,
          resolution: 1,
        });
        initialized = true;
        if (disposed || !hostRef.current) {
          destroy();
          return;
        }
        app.canvas.className = "flower-canvas";
        app.canvas.setAttribute("aria-label", `${spec.species} pixel flower`);
        hostRef.current.replaceChildren(app.canvas);

        flower = createPixelFlower(spec);
        flower.container.scale.set(3);
        app.stage.addChild(flower.container);
        let elapsedMs = 0;
        app.ticker.add((ticker) => {
          if (!pausedRef.current) elapsedMs += ticker.deltaMS;
          flower?.update(elapsedMs);
        });
      } catch (error) {
        if (disposed) return;
        console.error(`无法初始化 ${spec.species} 像素花`, error);
        hostRef.current?.replaceChildren(document.createTextNode("花朵渲染失败"));
      }
    };

    void mount();
    return () => {
      disposed = true;
      destroy();
    };
  }, [spec]);

  return <div ref={hostRef} className="canvas-host" data-testid={`flower-${spec.species}`} />;
}

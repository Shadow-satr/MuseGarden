import { useState } from "react";
import type { Interactable } from "../world/interactions";

interface WorldOverlayProps {
  target: Interactable | null;
  interactionMessage: string;
}

export function WorldOverlay({ target, interactionMessage }: WorldOverlayProps) {
  const [connected, setConnected] = useState(false);
  return <div className="world-overlay">
    <div className="world-title"><span>MUSEGARDEN</span><h1>音迹花园</h1></div>
    <div className="interaction-hint" role="status">
      {target && <span><kbd>E</kbd> {target.prompt}</span>}
      {interactionMessage && <small>{interactionMessage}</small>}
    </div>
    <button className="overlay-button" type="button" onClick={() => setConnected((value) => !value)}>
      {connected ? "UI Layer ✓" : "☰"}
    </button>
  </div>;
}

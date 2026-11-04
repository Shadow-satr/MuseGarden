import type { Interactable } from "../world/interactions";

interface WorldOverlayProps {
  target: Interactable | null;
  interactionMessage: string;
  onOpenGuide: () => void;
}

export function WorldOverlay({ target, interactionMessage, onOpenGuide }: WorldOverlayProps) {
  return <div className="world-overlay">
    <div className="world-title"><span>MUSEGARDEN</span><h1>音迹花园</h1></div>
    <div className="interaction-hint" role="status">
      {target && <div className="interaction-actions">
        <span><kbd>E</kbd> {target.prompt}</span>
        {target.kind === "flower" && <span><kbd>Delete</kbd> 删除花朵</span>}
      </div>}
      {interactionMessage && <small>{interactionMessage}</small>}
    </div>
    <button className="overlay-button" type="button" onClick={onOpenGuide} aria-label="打开新手指引">
      新手指引
    </button>
  </div>;
}

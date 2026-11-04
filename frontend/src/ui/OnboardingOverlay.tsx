interface OnboardingOverlayProps {
  onClose: () => void;
}

export function OnboardingOverlay({ onClose }: OnboardingOverlayProps) {
  return <div className="creation-backdrop onboarding-backdrop" role="presentation">
    <section className="creation-panel onboarding-panel" role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
      <p className="creation-eyebrow">MUSEGARDEN · WELCOME</p>
      <h2 id="onboarding-title">从一段记忆开始</h2>
      <p className="creation-description">在花园里走一走，找到空地，种下此刻想留下的声音。</p>
      <ol className="onboarding-steps">
        <li><kbd>WASD</kbd> 或方向键：在花园中移动。</li>
        <li>靠近空地或花朵后按 <kbd>E</kbd>：种下记忆或查看已有记忆。</li>
        <li>按 <kbd>M</kbd>：打开花园地图，查看当前位置和整体布局。</li>
        <li>靠近花朵后按 <kbd>Delete</kbd>：移除花朵，让土地重新可种植。</li>
      </ol>
      <div className="creation-actions">
        <button className="creation-submit" type="button" onClick={onClose}>开始探索</button>
      </div>
    </section>
  </div>;
}

import { useEffect, useRef, useState } from "react";

import { GardenCanvas } from "./game/flowers/GardenCanvas";
import { creationClient, type DemoCreation } from "./game/flowers/creationClient";
import { plantingClient } from "./game/flowers/plantingClient";
import type { GardenGridCell, GardenPreviewPayload, GardenRenderFlower } from "./game/flowers/types";

const SPECIES_NAMES: Record<string, string> = {
  rose: "玫瑰", peony: "牡丹", sunflower: "向日葵", tulip: "郁金香",
  hydrangea: "绣球", lily: "百合", daisy: "雏菊", lavender: "薰衣草",
  wildflower: "野花",
};
const displayPosition = (cell: GardenGridCell) => `(${cell.x + 1}, ${cell.y + 1})`;

function App() {
  const [payload, setPayload] = useState<GardenPreviewPayload | null>(null);
  const [creations, setCreations] = useState<DemoCreation[]>([]);
  const [activeCreation, setActiveCreation] = useState<DemoCreation | null>(null);
  const [selectedPlanting, setSelectedPlanting] = useState<GardenRenderFlower | null>(null);
  const [composerCell, setComposerCell] = useState<GardenGridCell | null>(null);
  const [highlightedCell, setHighlightedCell] = useState<GardenGridCell | null>(null);
  const [pendingDig, setPendingDig] = useState<GardenRenderFlower | null>(null);
  const [memoryText, setMemoryText] = useState("");
  const [modificationText, setModificationText] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [digging, setDigging] = useState(false);
  const [creationStage, setCreationStage] = useState("");
  const highlightTimer = useRef<number | null>(null);

  useEffect(() => {
    plantingClient.loadGarden().then(setPayload)
      .catch((reason) => setError(`花园数据加载失败：${String(reason)}`));
    creationClient.list().then(setCreations)
      .catch((reason) => setError(`记忆列表加载失败：${String(reason)}`));
    return () => {
      if (highlightTimer.current !== null) window.clearTimeout(highlightTimer.current);
    };
  }, []);

  const highlight = (cell: GardenGridCell, transient = false) => {
    if (highlightTimer.current !== null) window.clearTimeout(highlightTimer.current);
    setHighlightedCell(cell);
    if (transient) {
      highlightTimer.current = window.setTimeout(() => {
        setHighlightedCell((current) =>
          current?.x === cell.x && current?.y === cell.y ? null : current,
        );
        highlightTimer.current = null;
      }, 3500);
    }
  };

  const chooseGardenCell = (cell: GardenGridCell) => {
    if (!payload || creating || digging) return;
    setPendingDig(null);
    setError("");
    highlight(cell);
    const planted = payload.garden.flowers.find(
      (flower) => flower.grid_x === cell.x && flower.grid_y === cell.y,
    );
    if (planted) {
      setSelectedPlanting(planted);
      setComposerCell(null);
      setActiveCreation(creations.find(
        (item) => item.planting?.record_id === planted.planting_record_id,
      ) ?? null);
      setMessage(`${SPECIES_NAMES[planted.render_spec.species] ?? "花"}种在 ${displayPosition(cell)}。`);
      return;
    }
    setSelectedPlanting(null);
    setActiveCreation(null);
    setComposerCell(cell);
    setMessage(`已选择空地 ${displayPosition(cell)}。`);
  };

  const createMemory = async () => {
    if (!composerCell || !payload || !memoryText.trim() || creating) return;
    setCreating(true);
    setError("");
    setCreationStage("AI 正在理解这段记忆…");
    const stages = ["AI 正在理解这段记忆…", "正在生成音乐与花朵，请稍候…", "还在创作中；音频生成可能需要一段时间…"];
    let stageIndex = 0;
    const progressTimer = window.setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, stages.length - 1);
      setCreationStage(stages[stageIndex]);
    }, 8000);
    try {
      const creation = await creationClient.create(
        memoryText.trim(), payload.garden.garden_id, composerCell.x, composerCell.y,
      );
      setCreations((items) => [...items, creation]);
      setActiveCreation(creation);
      setComposerCell(null);
      setMemoryText("");
      setCreationStage("");
      setMessage(`新花已种在 ${displayPosition(composerCell)}。`);
      highlight(composerCell, true);
      try {
        const next = await plantingClient.loadGarden();
        setPayload(next);
        setSelectedPlanting(next.garden.flowers.find(
          (flower) => flower.planting_record_id === creation.planting?.record_id,
        ) ?? null);
      } catch (reason) {
        setError(`创作已保存，但画面刷新失败：${String(reason)}。请重新加载页面。`);
      }
    } catch (reason) {
      setError(`创作失败：${reason instanceof Error ? reason.message : String(reason)}`);
    } finally {
      window.clearInterval(progressTimer);
      setCreating(false);
    }
  };

  const regenerateMusic = async () => {
    if (!activeCreation || !modificationText.trim() || regenerating) return;
    setRegenerating(true);
    setError("");
    try {
      const updated = await creationClient.regenerate(activeCreation.creation_id, modificationText.trim());
      setActiveCreation(updated);
      setCreations((items) => items.map((item) => item.creation_id === updated.creation_id ? updated : item));
      setModificationText("");
    } catch (reason) {
      setError(`音乐修改失败：${reason instanceof Error ? reason.message : String(reason)}`);
    } finally {
      setRegenerating(false);
    }
  };

  const digUp = async () => {
    if (!pendingDig || !payload || digging) return;
    const removed = pendingDig;
    setDigging(true);
    setError("");
    try {
      await creationClient.digUp(payload.garden.garden_id, removed.planting_record_id);
      setPendingDig(null);
      setSelectedPlanting(null);
      setHighlightedCell(null);
      setMessage(`已永久铲除 ${displayPosition({ x: removed.grid_x, y: removed.grid_y })} 的花。`);
      if (activeCreation?.planting?.record_id === removed.planting_record_id) {
        setActiveCreation({ ...activeCreation, flower: null, planting: null });
      }
      try {
        const [nextGarden, nextCreations] = await Promise.all([plantingClient.loadGarden(), creationClient.list()]);
        setPayload(nextGarden);
        setCreations(nextCreations);
        setActiveCreation((current) => nextCreations.find((item) => item.creation_id === current?.creation_id) ?? current);
      } catch (reason) {
        setError(`花已永久铲除，但画面刷新失败：${String(reason)}。请重新加载页面。`);
      }
    } catch (reason) {
      setError(`铲除失败：${reason instanceof Error ? reason.message : String(reason)}`);
    } finally {
      setDigging(false);
    }
  };

  const garden = payload?.garden;
  const archived = creations.filter((item) => !item.planting);

  return <main className="app-shell">
    <header className="garden-hero">
      <div>
        <p className="eyebrow">MUSEGARDEN · ENGINEERING PREVIEW</p>
        <h1>让一段记忆开花、唱歌</h1>
        <p className="intro">点击空地写下一句话；点击已种的花查看记忆，或用铲子将它永久移出花园。</p>
      </div>
      <div className="status-chip">{creating ? "创作中" : digging ? "铲除中" : "预览中"}</div>
    </header>

    {error && !garden && <p className="error-message">{error}</p>}
    {!error && !garden && <p className="loading-message">正在读取花园…</p>}

    {garden && payload && <>
      <section className="garden-summary" aria-label="花园概要">
        <div><strong>{garden.flowers.length}</strong><span>朵记忆花</span></div>
        <div><strong>{garden.grid_width} × {garden.grid_height}</strong><span>花园格子</span></div>
        <div><strong>{highlightedCell ? displayPosition(highlightedCell) : "—"}</strong><span>选中位置（从 1,1 开始）</span></div>
      </section>

      <section className="garden-frame" aria-label="MuseGarden 花园预览">
        <div className="frame-topline"><div><p>GARDEN PREVIEW</p><h2>暮色记忆圃</h2></div><code>{garden.pixel_width} × {garden.pixel_height}</code></div>
        <div className="garden-viewport"><GardenCanvas spec={garden} highlight={highlightedCell} onGridClick={chooseGardenCell} /></div>
      </section>
      <p className="garden-instruction">坐标从 (1,1) 显示。选地会高亮；新花种下后高亮约 3.5 秒，点击别处立即切换。</p>

      {composerCell && <section className="creation-panel" aria-label="创作记忆">
        <div className="creation-panel-head"><div><small>NEW MEMORY · {displayPosition(composerCell)}</small><h2>这一刻，你想留下什么？</h2></div>
          <button className="quiet-button" disabled={creating} onClick={() => setComposerCell(null)}>关闭</button></div>
        <textarea aria-label="记忆文字" placeholder="例如：比赛结束后终于松了一口气，也很开心" value={memoryText}
          onChange={(event) => setMemoryText(event.target.value)} maxLength={2000} disabled={creating} />
        <div className="creation-panel-actions"><span role="status">{creating ? creationStage : "将生成音乐和花，并种在高亮位置。"}</span>
          <button className="primary-button" disabled={creating || !memoryText.trim()} onClick={() => void createMemory()}>
            {creating ? "创作中…" : "Create · 生成记忆"}</button></div>
      </section>}

      {activeCreation && <section className="creation-panel result-panel" aria-label="创作结果">
        <div className="creation-panel-head"><div><small>MEMORY · {activeCreation.flower?.species ?? "花已铲除"}</small><h2>{activeCreation.text}</h2></div>
          <span className="result-badge">{activeCreation.planting ? `🌸 花已种在 ${displayPosition(activeCreation.planting)}` : "花已永久铲除 · 记忆保留"}</span></div>
        <p>情绪：{activeCreation.blueprint.primary_emotion} · 音乐版本 V{activeCreation.music.version}</p>
        <audio key={activeCreation.music.artifact_id} controls src={activeCreation.music.url} aria-label="创作音乐" />
        <div className="music-edit-row"><input aria-label="音乐修改要求" placeholder="例如：更温暖一点" value={modificationText}
          onChange={(event) => setModificationText(event.target.value)} disabled={regenerating} />
          <button className="primary-button" disabled={regenerating || !modificationText.trim()} onClick={() => void regenerateMusic()}>
            {regenerating ? "正在生成新版音乐…" : "修改音乐"}</button></div>
        <small>铲除花朵不会删除这段记忆或音乐。</small>
      </section>}

      {selectedPlanting && <section className="planting-panel" aria-label="花朵操作">
        <strong>{SPECIES_NAMES[selectedPlanting.render_spec.species] ?? "花"} · {displayPosition({ x: selectedPlanting.grid_x, y: selectedPlanting.grid_y })}</strong>
        <button className="shovel-button" disabled={digging} onClick={() => setPendingDig(selectedPlanting)}>🪏 铲除这朵花</button>
      </section>}

      {pendingDig && <section className="confirm-panel" role="dialog" aria-modal="true" aria-label="确认永久铲除">
        <h2>确定永久铲除这朵花吗？</h2>
        <p>位置 {displayPosition({ x: pendingDig.grid_x, y: pendingDig.grid_y })} 的花和种植记录将被删除，无法恢复。记忆与音乐会保留。</p>
        <div className="button-row"><button className="quiet-button" disabled={digging} onClick={() => setPendingDig(null)}>取消</button>
          <button className="danger-button" disabled={digging} onClick={() => void digUp()}>{digging ? "正在铲除…" : "确认永久铲除"}</button></div>
      </section>}

      {(message || error) && <section className="notice-panel" aria-live="polite">{message && <span>{message}</span>}{error && <span role="alert">{error}</span>}</section>}

      {archived.length > 0 && <section className="memory-archive" aria-label="保留的记忆"><h2>保留的记忆</h2>
        <p>这里的花已永久铲除，文字与音乐仍在。</p>
        {archived.map((item) => <button key={item.creation_id} className="quiet-button"
          onClick={() => { setActiveCreation(item); setSelectedPlanting(null); setComposerCell(null); setHighlightedCell(null); }}>{item.text}</button>)}
      </section>}
    </>}
    <footer>MusicBlueprint → AudioArtifact + FlowerArtifact → Garden</footer>
  </main>;
}

export default App;

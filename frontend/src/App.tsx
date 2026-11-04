import { useCallback, useEffect, useRef, useState } from "react";

import {
  createMemory, CreationResponseError, loadFlowerMemory, removeFlowerFromGarden, renameFlowerMusicVersion, reviseFlowerMusic, selectFlowerMusicVersion,
  type CreationDraft, type CreationResult, type FlowerMemory,
} from "./api/creation";
import { GardenWorldView } from "./components/GardenWorldView";
import { MapOverview } from "./components/MapOverview";
import { CreationOverlay, type CreationStatus } from "./ui/CreationOverlay";
import { FlowerDetailOverlay } from "./ui/FlowerDetailOverlay";
import { MiniMapOverlay } from "./ui/MiniMapOverlay";
import { OnboardingOverlay } from "./ui/OnboardingOverlay";
import { WorldOverlay } from "./ui/WorldOverlay";
import type { Interactable } from "./world/interactions";
import type { GardenWorld } from "./world/GardenWorld";

function GardenApp() {
  const [target, setTarget] = useState<Interactable | null>(null);
  const [selectedPlantSpot, setSelectedPlantSpot] = useState<Extract<Interactable, { kind: "plant-spot" }> | null>(null);
  const [interactionMessage, setInteractionMessage] = useState("");
  const [creationStatus, setCreationStatus] = useState<CreationStatus>("idle");
  const [creationResult, setCreationResult] = useState<CreationResult | null>(null);
  const [creationError, setCreationError] = useState("");
  const [selectedFlower, setSelectedFlower] = useState<Extract<Interactable, { kind: "flower" }> | null>(null);
  const [flowerMemory, setFlowerMemory] = useState<FlowerMemory | null>(null);
  const [flowerDetailStatus, setFlowerDetailStatus] = useState<"loading" | "success" | "error">("loading");
  const [flowerDetailError, setFlowerDetailError] = useState("");
  const [revisionStatus, setRevisionStatus] = useState<"idle" | "loading" | "error">("idle");
  const [revisionError, setRevisionError] = useState("");
  const [selectingAudioId, setSelectingAudioId] = useState<string | null>(null);
  const [mapOpen, setMapOpen] = useState(false);
  const [mapPlayerPosition, setMapPlayerPosition] = useState<{ x: number; y: number } | null>(null);
  const [guideOpen, setGuideOpen] = useState(() => window.localStorage.getItem("musegarden-onboarding-complete") !== "true");
  const pendingRequest = useRef<AbortController | null>(null);
  const deleteRequest = useRef<AbortController | null>(null);
  const flowerDetailRequest = useRef<AbortController | null>(null);
  const musicRequest = useRef<AbortController | null>(null);
  const worldRef = useRef<GardenWorld | null>(null);
  const overlayOpen = selectedPlantSpot !== null || selectedFlower !== null || guideOpen;
  const onWorldReady = useCallback((world: GardenWorld | null) => { worldRef.current = world; }, []);
  const onCloseGuide = useCallback(() => {
    window.localStorage.setItem("musegarden-onboarding-complete", "true");
    setGuideOpen(false);
  }, []);
  useEffect(() => () => {
    pendingRequest.current?.abort();
    pendingRequest.current = null;
    deleteRequest.current?.abort();
    deleteRequest.current = null;
    flowerDetailRequest.current?.abort();
    flowerDetailRequest.current = null;
    musicRequest.current?.abort();
    musicRequest.current = null;
  }, []);
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.repeat || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.target instanceof HTMLElement && event.target.closest("input, textarea, [contenteditable='true']")) return;
      if (event.key === "Escape" && mapOpen) {
        event.preventDefault();
        setMapOpen(false);
        return;
      }
      if (event.key.toLowerCase() !== "m" || overlayOpen) return;
      event.preventDefault();
      if (!mapOpen) setMapPlayerPosition(worldRef.current?.playerWorldPosition ?? null);
      setMapOpen((open) => !open);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mapOpen, overlayOpen]);
  const onTargetChange = useCallback((next: Interactable | null) => {
    setTarget(next);
    setInteractionMessage("");
  }, []);
  const readFlowerMemory = useCallback(async (flower: Extract<Interactable, { kind: "flower" }>) => {
    flowerDetailRequest.current?.abort();
    const controller = new AbortController();
    flowerDetailRequest.current = controller;
    setFlowerDetailStatus("loading");
    setFlowerDetailError("");
    setFlowerMemory(null);
    setRevisionStatus("idle");
    setRevisionError("");
    setSelectingAudioId(null);
    try {
      const memory = await loadFlowerMemory(flower.plantingRecordId, flower.flowerArtifactId, controller.signal);
      if (flowerDetailRequest.current !== controller) return;
      setFlowerMemory(memory);
      setFlowerDetailStatus("success");
    } catch (error) {
      if (flowerDetailRequest.current !== controller || controller.signal.aborted) return;
      setFlowerDetailError(error instanceof Error ? error.message : "记忆详情加载失败");
      setFlowerDetailStatus("error");
    } finally {
      if (flowerDetailRequest.current === controller) flowerDetailRequest.current = null;
    }
  }, []);
  const onInteract = useCallback((current: Interactable) => {
    if (current.kind === "plant-spot") {
      setSelectedPlantSpot(current);
      setInteractionMessage("");
      setCreationStatus("idle");
      setCreationResult(null);
      setCreationError("");
    } else {
      setSelectedFlower(current);
      setInteractionMessage("");
      void readFlowerMemory(current);
    }
  }, [readFlowerMemory]);
  const onDeleteFlower = useCallback(async (flower: Extract<Interactable, { kind: "flower" }>) => {
    if (deleteRequest.current) return;
    const world = worldRef.current;
    const gardenId = world?.currentGardenId;
    if (!world || !gardenId) {
      setInteractionMessage("花园尚未就绪，暂时无法删除花朵。");
      return;
    }
    const controller = new AbortController();
    deleteRequest.current = controller;
    setInteractionMessage("正在移除花朵…");
    try {
      await removeFlowerFromGarden(gardenId, flower.plantingRecordId, controller.signal);
      if (deleteRequest.current !== controller) return;
      await world.refreshGarden(undefined, controller.signal);
      if (deleteRequest.current === controller) {
        setInteractionMessage("花朵已移除，这块地可以重新种下记忆。");
      }
    } catch (error) {
      if (deleteRequest.current !== controller || controller.signal.aborted) return;
      setInteractionMessage(error instanceof Error ? `删除失败：${error.message}` : "删除失败，请重试。");
    } finally {
      if (deleteRequest.current === controller) deleteRequest.current = null;
    }
  }, []);
  const onCloseFlowerDetail = useCallback(() => {
    flowerDetailRequest.current?.abort();
    flowerDetailRequest.current = null;
    musicRequest.current?.abort();
    musicRequest.current = null;
    setSelectedFlower(null);
    setFlowerMemory(null);
    setFlowerDetailError("");
    setRevisionStatus("idle");
    setRevisionError("");
    setSelectingAudioId(null);
    setInteractionMessage("");
  }, []);
  const onReviseFlowerMusic = useCallback(async (modificationText: string): Promise<boolean> => {
    const memory = flowerMemory;
    if (!memory || musicRequest.current) return false;
    const controller = new AbortController();
    musicRequest.current = controller;
    setRevisionStatus("loading");
    setRevisionError("");
    try {
      const updated = await reviseFlowerMusic(memory.creation_id, modificationText, controller.signal);
      if (musicRequest.current !== controller) return false;
      setFlowerMemory(updated);
      setRevisionStatus("idle");
      return true;
    } catch (error) {
      if (musicRequest.current !== controller || controller.signal.aborted) return false;
      setRevisionError(error instanceof Error ? error.message : "新版音乐生成失败");
      setRevisionStatus("error");
      return false;
    } finally {
      if (musicRequest.current === controller) musicRequest.current = null;
    }
  }, [flowerMemory]);
  const onSelectFlowerMusic = useCallback(async (audioArtifactId: string): Promise<void> => {
    const memory = flowerMemory;
    if (!memory || musicRequest.current || memory.music?.artifact_id === audioArtifactId) return;
    const controller = new AbortController();
    musicRequest.current = controller;
    setSelectingAudioId(audioArtifactId);
    setRevisionStatus("idle");
    setRevisionError("");
    try {
      const updated = await selectFlowerMusicVersion(memory.creation_id, audioArtifactId, controller.signal);
      if (musicRequest.current === controller) {
        setFlowerMemory(updated);
        setRevisionStatus("idle");
      }
    } catch (error) {
      if (musicRequest.current === controller && !controller.signal.aborted) {
        setRevisionError(error instanceof Error ? error.message : "音乐版本切换失败");
        setRevisionStatus("error");
      }
    } finally {
      if (musicRequest.current === controller) {
        musicRequest.current = null;
        setSelectingAudioId(null);
      }
    }
  }, [flowerMemory]);
  const onRenameFlowerMusic = useCallback(async (audioArtifactId: string, displayName: string): Promise<boolean> => {
    const memory = flowerMemory;
    if (!memory || musicRequest.current) return false;
    const controller = new AbortController();
    musicRequest.current = controller;
    setRevisionError("");
    try {
      const updated = await renameFlowerMusicVersion(memory.creation_id, audioArtifactId, displayName, controller.signal);
      if (musicRequest.current === controller) setFlowerMemory(updated);
      return true;
    } catch (error) {
      if (musicRequest.current === controller && !controller.signal.aborted) {
        setRevisionError(error instanceof Error ? error.message : "版本名称保存失败");
        setRevisionStatus("error");
      }
      return false;
    } finally {
      if (musicRequest.current === controller) musicRequest.current = null;
    }
  }, [flowerMemory]);
  const onCancelCreation = useCallback(() => {
    pendingRequest.current?.abort();
    pendingRequest.current = null;
    setSelectedPlantSpot(null);
    setInteractionMessage("");
    setCreationStatus("idle");
    setCreationResult(null);
    setCreationError("");
  }, []);
  const onCreate = useCallback(async (draft: CreationDraft) => {
    if (pendingRequest.current) return;
    const world = worldRef.current;
    const gardenId = world?.currentGardenId;
    if (!world || !gardenId) {
      setCreationError("花园尚未就绪，请稍后重试");
      setCreationStatus("error");
      return;
    }
    const controller = new AbortController();
    pendingRequest.current = controller;
    setCreationStatus("loading");
    setCreationError("");
    try {
      const result = await createMemory(gardenId, draft, controller.signal);
      if (pendingRequest.current !== controller) return;
      setCreationResult(result);
      setCreationStatus("syncing");
      try {
        await world.refreshGarden({
          recordId: result.planting.record_id,
          flowerArtifactId: result.flower.artifact_id,
          x: result.planting.x,
          y: result.planting.y,
        }, controller.signal);
        if (pendingRequest.current === controller) setCreationStatus("success");
      } catch (error) {
        if (pendingRequest.current !== controller) return;
        setCreationError(error instanceof Error ? error.message : "花园刷新失败");
        setCreationStatus("refresh-error");
      }
    } catch (error) {
      if (pendingRequest.current !== controller) return;
      if (error instanceof CreationResponseError) {
        try { await world.refreshGarden(undefined, controller.signal); } catch { /* Keep the original response error. */ }
        if (pendingRequest.current !== controller) return;
        setCreationError(error.message);
        setCreationStatus("result-error");
        return;
      }
      setCreationError(error instanceof Error ? error.message : "提交失败，请重试");
      setCreationStatus("error");
    } finally {
      if (pendingRequest.current === controller) pendingRequest.current = null;
    }
  }, []);
  const onRetryRefresh = useCallback(async () => {
    const world = worldRef.current;
    const result = creationResult;
    if (!world || !result || pendingRequest.current) return;
    const controller = new AbortController();
    pendingRequest.current = controller;
    setCreationStatus("syncing");
    setCreationError("");
    try {
      await world.refreshGarden({
        recordId: result.planting.record_id,
        flowerArtifactId: result.flower.artifact_id,
        x: result.planting.x,
        y: result.planting.y,
      }, controller.signal);
      if (pendingRequest.current === controller) setCreationStatus("success");
    } catch (error) {
      if (pendingRequest.current === controller) {
        setCreationError(error instanceof Error ? error.message : "花园刷新失败");
        setCreationStatus("refresh-error");
      }
    } finally {
      if (pendingRequest.current === controller) pendingRequest.current = null;
    }
  }, [creationResult]);
  return <main className="world-shell">
    <WorldOverlay target={overlayOpen ? null : target} interactionMessage={interactionMessage} onOpenGuide={() => setGuideOpen(true)} />
    <GardenWorldView onTargetChange={onTargetChange} onInteract={onInteract} onDeleteFlower={onDeleteFlower} onReady={onWorldReady} paused={overlayOpen || mapOpen} />
    {selectedPlantSpot && <CreationOverlay
      plantSpotId={selectedPlantSpot.id}
      status={creationStatus}
      result={creationResult}
      error={creationError}
      onCancel={onCancelCreation}
      onCreate={onCreate}
      onRetryRefresh={onRetryRefresh}
    />}
    {selectedFlower && <FlowerDetailOverlay
      status={flowerDetailStatus}
      memory={flowerMemory}
      error={flowerDetailError}
      revisionStatus={revisionStatus}
      revisionError={revisionError}
      selectingAudioId={selectingAudioId}
      onClose={onCloseFlowerDetail}
      onRetry={() => { void readFlowerMemory(selectedFlower); }}
      onRevise={onReviseFlowerMusic}
      onSelectVersion={onSelectFlowerMusic}
      onRenameVersion={onRenameFlowerMusic}
    />}
    {mapOpen && <MiniMapOverlay playerPosition={mapPlayerPosition} />}
    {guideOpen && <OnboardingOverlay onClose={onCloseGuide} />}
  </main>;
}

function App() {
  return window.location.pathname === "/map-overview" ? <MapOverview /> : <GardenApp />;
}

export default App;

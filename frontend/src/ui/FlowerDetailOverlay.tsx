import { useState, type FormEvent } from "react";

import type { FlowerMemory } from "../api/creation";
import { AudioPlayer } from "./AudioPlayer";
import { FlowerPortrait } from "./FlowerPortrait";

interface FlowerDetailOverlayProps {
  status: "loading" | "success" | "error";
  memory: FlowerMemory | null;
  error: string;
  revisionStatus: "idle" | "loading" | "error";
  revisionError: string;
  selectingAudioId: string | null;
  onClose: () => void;
  onRetry: () => void;
  onRevise: (modificationText: string) => Promise<boolean>;
  onSelectVersion: (audioArtifactId: string) => Promise<void>;
}

const MAX_REVISION_LENGTH = 500;

export function FlowerDetailOverlay({
  status, memory, error, revisionStatus, revisionError, selectingAudioId,
  onClose, onRetry, onRevise, onSelectVersion,
}: FlowerDetailOverlayProps) {
  const [editing, setEditing] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [expandedVersionId, setExpandedVersionId] = useState<string | null>(null);
  const busy = revisionStatus === "loading" || selectingAudioId !== null;

  const submitRevision = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const text = instruction.trim();
    if (!text || busy) return;
    if (await onRevise(text)) {
      setInstruction("");
      setEditing(false);
    }
  };

  return <div className="creation-backdrop">
    <section className="creation-panel flower-detail-panel" role="dialog" aria-modal="true" aria-labelledby="flower-detail-title">
      <p className="creation-eyebrow">MUSEGARDEN · FLOWER MEMORY</p>
      <h2 id="flower-detail-title">这朵花的记忆</h2>

      {status === "loading" && <p className="flower-detail-loading" role="status">正在找回这段记忆……</p>}

      {status === "error" && <div className="flower-detail-error">
        <p className="creation-feedback creation-error" role="alert">{error}</p>
        <div className="creation-actions">
          <button className="creation-submit" type="button" onClick={onRetry}>重新读取</button>
          <button className="creation-cancel" type="button" onClick={onClose}>返回花园</button>
        </div>
      </div>}

      {status === "success" && memory && <div className="creation-result">
        <FlowerPortrait species={memory.flower.species} renderSpec={memory.flower.render_spec} />
        <p className="flower-detail-species">{memory.flower.species}</p>
        <blockquote>{memory.text}</blockquote>

        <section className="music-version-section" aria-labelledby="music-version-title">
          <div className="music-version-heading">
            <div>
              <p className="creation-eyebrow">MUSIC VERSIONS</p>
              <h3 id="music-version-title">音乐版本</h3>
            </div>
            {!editing && <button className="music-revise-button" type="button" disabled={busy} onClick={() => setEditing(true)}>修改音乐</button>}
          </div>

          <div className="music-version-list">
            {memory.music_versions.map((version) => {
              const description = version.modification_text || (version.version === 1 ? "初始版本" : "历史版本");
              const expanded = expandedVersionId === version.version_id;
              return <div className={`music-version-item${version.is_selected ? " is-selected" : ""}`} key={version.version_id}>
                <button
                  className="music-version-select"
                  type="button"
                  aria-label={`选择 V${version.version} 音乐`}
                  aria-pressed={version.is_selected}
                  disabled={busy || version.is_selected}
                  onClick={() => { void onSelectVersion(version.audio_artifact_id); }}
                >
                  <strong>V{version.version}</strong>{version.is_latest && <small>最新</small>}
                </button>
                <button
                  className={`music-version-instruction${expanded ? " is-expanded" : ""}`}
                  type="button"
                  aria-expanded={expanded}
                  aria-label={`${expanded ? "收起" : "展开"} V${version.version} 修改要求`}
                  onClick={() => setExpandedVersionId(expanded ? null : version.version_id)}
                >{description}</button>
                <button
                  className="music-version-select music-version-status"
                  type="button"
                  aria-label={`选择 V${version.version} 音乐`}
                  disabled={busy || version.is_selected}
                  onClick={() => { void onSelectVersion(version.audio_artifact_id); }}
                >{selectingAudioId === version.audio_artifact_id ? "切换中…" : version.is_selected ? "当前播放" : "选择试听"}</button>
                {expanded && <p className="music-version-full-instruction">{description}</p>}
              </div>;
            })}
          </div>

          {memory.music?.url
            ? <AudioPlayer key={memory.music.artifact_id} url={memory.music.url} />
            : <p className="creation-feedback creation-error" role="alert">这段记忆暂时没有可播放的音乐</p>}
          {!editing && revisionStatus === "error" && <p className="creation-feedback creation-error" role="alert">{revisionError}</p>}

          {editing && <form className="music-revision-form" onSubmit={(event) => { void submitRevision(event); }}>
            <p className="creation-description">告诉花园，希望这段音乐发生什么变化。原始记忆不会被修改。</p>
            <label className="creation-label" htmlFor="music-revision-instruction">修改要求</label>
            <textarea
              id="music-revision-instruction"
              value={instruction}
              maxLength={MAX_REVISION_LENGTH}
              disabled={revisionStatus === "loading"}
              onChange={(event) => setInstruction(event.target.value.slice(0, MAX_REVISION_LENGTH))}
              placeholder="例如，整体更轻快一些，保留钢琴，减少鼓点……"
              rows={4}
              autoFocus
            />
            <div className="creation-count">{instruction.length} / {MAX_REVISION_LENGTH}</div>
            {revisionStatus === "loading" && <p className="creation-feedback" role="status">正在调整你的音乐……</p>}
            {revisionStatus === "error" && <p className="creation-feedback creation-error" role="alert">{revisionError}</p>}
            <div className="creation-actions music-revision-actions">
              <button className="creation-submit" type="submit" disabled={!instruction.trim() || busy}>
                {revisionStatus === "error" ? "重新生成" : "生成新版音乐"}
              </button>
              <button className="creation-cancel" type="button" disabled={revisionStatus === "loading"} onClick={() => setEditing(false)}>取消</button>
            </div>
          </form>}
        </section>

        <div className="creation-actions">
          <button className="creation-submit" type="button" disabled={revisionStatus === "loading"} onClick={onClose}>返回花园</button>
        </div>
      </div>}
    </section>
  </div>;
}

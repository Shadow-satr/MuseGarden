import { useEffect, useRef, useState, type FormEvent } from "react";

import type { CreationDraft, CreationResult } from "../api/creation";
import { AudioPlayer } from "./AudioPlayer";

export type CreationStatus = "idle" | "loading" | "syncing" | "success" | "error" | "refresh-error" | "result-error";

interface CreationOverlayProps {
  plantSpotId: string;
  status: CreationStatus;
  result: CreationResult | null;
  error: string;
  onCancel: () => void;
  onCreate: (draft: CreationDraft) => void;
  onRetryRefresh: () => void;
}

const MAX_LENGTH = 500;

export function CreationOverlay({ plantSpotId, status, result, error, onCancel, onCreate, onRetryRefresh }: CreationOverlayProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const memory = text.trim();
    if (!memory || status === "loading" || status === "syncing" || status === "success" || status === "refresh-error" || status === "result-error") return;
    onCreate({ plantSpotId, text: memory });
  };

  return <div className="creation-backdrop">
    <section className="creation-panel memory-creation-panel" role="dialog" aria-modal="true" aria-labelledby="creation-title">
      <p className="creation-eyebrow">MUSEGARDEN · MEMORY</p>
      <h2 id="creation-title">留下一段记忆</h2>
      {result ? <div className="creation-result" role="status">
        <p className="creation-flower-icon" aria-hidden="true">🌸</p>
        <p>{status === "success" ? "你的记忆已经种下了" : "记忆已生成，正在更新花园……"}</p>
        <blockquote>{result.text}</blockquote>
        {status === "success" && <AudioPlayer url={result.music.url} />}
        {status === "refresh-error" && <p className="creation-feedback creation-error" role="alert">花已种下，但画面更新失败：{error}</p>}
        <div className="creation-actions">
          {status === "refresh-error" && <button className="creation-submit" type="button" onClick={onRetryRefresh}>重试刷新</button>}
          {status === "success" && <button className="creation-submit" type="button" onClick={onCancel}>完成</button>}
          {status !== "success" && <button className="creation-cancel" type="button" onClick={onCancel}>返回花园</button>}
        </div>
      </div> : <>
      <p className="creation-description">这一刻，你想留下什么？</p>
      <form onSubmit={submit}>
        <label className="creation-label" htmlFor="creation-memory">写下这段记忆</label>
        <textarea
          id="creation-memory"
          ref={textareaRef}
          value={text}
          maxLength={MAX_LENGTH}
          disabled={status === "loading"}
          onChange={(event) => setText(event.target.value.slice(0, MAX_LENGTH))}
          placeholder="比如，今天终于完成了比赛，感觉特别开心……"
          rows={6}
        />
        <div className="creation-count">{text.length} / {MAX_LENGTH}</div>
        {status === "loading" && <p className="creation-feedback" role="status">正在创造你的记忆……</p>}
        {status === "error" && <p className="creation-feedback creation-error" role="alert">{error}</p>}
        {status === "result-error" && <p className="creation-feedback creation-error" role="alert">{error}。后端可能已完成创作，请回到花园检查；不要重复提交。</p>}
        <div className="creation-actions">
          <button className="creation-submit" type="submit" disabled={!text.trim() || status === "loading" || status === "result-error"}>
            {status === "error" ? "重新尝试" : "开始创作"}
          </button>
          <button className="creation-cancel" type="button" onClick={onCancel}>{status === "result-error" ? "返回花园" : "取消"}</button>
        </div>
      </form>
      </>}
    </section>
  </div>;
}

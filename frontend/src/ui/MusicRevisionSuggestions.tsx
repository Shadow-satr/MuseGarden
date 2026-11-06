import { useEffect, useRef, useState } from "react";

import { generateMusicRevisionSuggestions, type MusicRevisionSuggestion } from "../api/creation";

interface MusicRevisionSuggestionsProps {
  audioArtifactId: string;
  onUseSuggestion: (text: string) => void;
}

export function MusicRevisionSuggestions({ audioArtifactId, onUseSuggestion }: MusicRevisionSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<MusicRevisionSuggestion[]>([]);
  const [seenTitles, setSeenTitles] = useState<string[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const requestVersion = useRef(0);

  useEffect(() => {
    setSuggestions([]);
    setSeenTitles([]);
    setStatus("idle");
    return () => { requestVersion.current += 1; };
  }, [audioArtifactId]);

  const refresh = async () => {
    setStatus("loading");
    const request = ++requestVersion.current;
    try {
      const next = await generateMusicRevisionSuggestions(audioArtifactId, seenTitles);
      if (request !== requestVersion.current) return;
      setSuggestions(next);
      setSeenTitles((previous) => [...previous, ...next.map((item) => item.title)].slice(-12));
      setStatus("idle");
    } catch {
      if (request !== requestVersion.current) return;
      setStatus("error");
    }
  };

  return <section className="music-suggestions" aria-labelledby="music-suggestions-title">
    <div className="music-suggestions-heading">
      <div><p className="creation-eyebrow">MUSIC IDEAS</p><h4 id="music-suggestions-title">不知道怎么改？</h4></div>
      <button type="button" onClick={() => { void refresh(); }} disabled={status === "loading"}>
        {status === "loading" ? "正在构思…" : suggestions.length ? "换一组建议" : "给我 3 条建议"}
      </button>
    </div>
    {status === "error" && <p className="creation-feedback creation-error">暂时无法根据当前音乐解读生成建议，请重试。</p>}
    {suggestions.length > 0 && <div className="music-suggestion-list">
      {suggestions.map((item) => <article key={item.title}>
        <h5>{item.title}</h5><p>{item.rationale}</p>
        <button type="button" onClick={() => onUseSuggestion(item.modification_text)}>采用这条建议</button>
      </article>)}
    </div>}
    <p className="music-companion-hint">也可以直接在下方写下你的想法。</p>
  </section>;
}

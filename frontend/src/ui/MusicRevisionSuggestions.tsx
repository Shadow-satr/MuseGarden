import { useEffect, useState } from "react";

import { generateMusicRevisionSuggestions, type MusicRevisionSuggestion } from "../api/creation";

interface MusicRevisionSuggestionsProps {
  audioArtifactId: string;
  onUseSuggestion: (text: string) => void;
}

export function MusicRevisionSuggestions({ audioArtifactId, onUseSuggestion }: MusicRevisionSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<MusicRevisionSuggestion[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  useEffect(() => { setSuggestions([]); setStatus("idle"); }, [audioArtifactId]);

  const refresh = async () => {
    setStatus("loading");
    try {
      setSuggestions(await generateMusicRevisionSuggestions(audioArtifactId, suggestions.map((item) => item.title)));
      setStatus("idle");
    } catch {
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
    {status === "error" && <p className="creation-feedback creation-error">建议暂时无法生成，请稍后再试。</p>}
    {suggestions.length > 0 && <div className="music-suggestion-list">
      {suggestions.map((item) => <article key={item.title}>
        <h5>{item.title}</h5><p>{item.rationale}</p>
        <button type="button" onClick={() => onUseSuggestion(item.modification_text)}>采用这条建议</button>
      </article>)}
    </div>}
    <p className="music-companion-hint">也可以直接在下方写下你的想法。</p>
  </section>;
}

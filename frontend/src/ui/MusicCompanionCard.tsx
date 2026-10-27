import { useEffect, useState } from "react";

import {
  generateMusicCompanionInterpretation,
  type MusicCompanionInterpretation,
} from "../api/creation";

interface MusicCompanionCardProps {
  audioArtifactId: string;
  version: number | undefined;
  modificationText: string | null | undefined;
}

const statusLabel: Record<string, string> = {
  blueprint_and_audio: "设定 + 音色线索",
  audio_tendency: "音色线索",
  blueprint_only: "编配设定",
  uncertain: "暂不确定",
};

const assessmentLabel: Record<string, string> = {
  supported: "得到支持",
  partially_supported: "部分得到支持",
  uncertain: "暂不确定",
  not_supported: "未得到支持",
};

export function MusicCompanionCard({ audioArtifactId, version, modificationText }: MusicCompanionCardProps) {
  const [result, setResult] = useState<MusicCompanionInterpretation | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    setResult(null);
    setStatus("idle");
    setError("");
  }, [audioArtifactId]);

  const generate = async () => {
    setStatus("loading");
    setError("");
    try {
      setResult(await generateMusicCompanionInterpretation(audioArtifactId));
      setStatus("idle");
    } catch (reason) {
      setStatus("error");
      setError(reason instanceof Error ? reason.message : "音乐解读暂时无法生成");
    }
  };

  useEffect(() => { void generate(); }, [audioArtifactId]);

  return <section className="music-companion-card" aria-labelledby="music-companion-title">
    <div className="music-companion-heading">
      <div>
        <p className="creation-eyebrow">MUSIC COMPANION</p>
        <h3 id="music-companion-title">音乐解读</h3>
      </div>
    </div>

    {!result && status === "loading" && <p className="music-companion-hint">正在整理这首音乐的完整解读…</p>}
    {status === "error" && <p className="creation-feedback creation-error" role="alert">{error}</p>}

    {result && <div className="music-companion-content">
      <p className="music-companion-introduction">{result.narrative.professional_introduction}</p>
      <p className="music-companion-character">{result.narrative.mood_and_character}</p>

      {version && version > 1 && modificationText && <section className="music-companion-difference" aria-label={`V${version} 相对上一版的变化`}>
        <h4>相对上一版</h4>
        <p>这次修改：{modificationText}</p>
        {result.narrative.intent_alignment.map((item) => <p key={item.intent}>
          <strong>{assessmentLabel[item.assessment] ?? "需进一步确认"}</strong>：{item.explanation}
        </p>)}
      </section>}

      <section>
        <h4>编配构成</h4>
        <ul className="music-companion-instruments">
          {result.narrative.instrumentation.map((item) => <li key={item.instrument}>
            <strong>{item.instrument}</strong><span>{statusLabel[item.evidence_status] ?? "线索"}</span><p>{item.description}</p>
          </li>)}
        </ul>
      </section>

      <section>
        <h4>分段聆听</h4>
        <ol className="music-companion-guide">
          {result.narrative.listening_guide.map((item) => <li key={item.section}>
            <strong>{item.section} · {item.start_seconds.toFixed(1)}–{item.end_seconds.toFixed(1)} 秒</strong><p>{item.description}</p>
          </li>)}
        </ol>
      </section>

      <p className="music-companion-caveat">{result.narrative.caveats[0]}</p>
    </div>}
  </section>;
}

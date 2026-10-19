import { useEffect, useRef, useState } from "react";

export function AudioPlayer({ url }: { url: string }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => () => { audioRef.current?.pause(); }, [url]);

  const toggle = async () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }
    try {
      await audio.play();
      setPlaying(true);
      setError("");
    } catch {
      setError("音乐暂时无法播放");
    }
  };

  return <div className="creation-audio">
    <audio ref={audioRef} src={url} preload="none" onEnded={() => setPlaying(false)} onError={() => setError("音乐加载失败")} />
    <button type="button" onClick={() => { void toggle(); }}>{playing ? "⏸ 暂停音乐" : "▶ 播放音乐"}</button>
    {error && <p role="alert">{error}</p>}
  </div>;
}

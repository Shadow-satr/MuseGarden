"""使用 librosa 对真实 WAV 做基础、可解释的声学分析。"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from uuid import UUID

from music_companion.schema import (
    AcousticFeatures,
    AudioAnalysisResult,
    AudioTimeSegment,
    FeatureStatistics,
)
from music_engine.audio_store import AudioStore


ANALYSIS_VERSION = "music-companion-step1-librosa-v1"
_SILENCE_PEAK_THRESHOLD = 1e-5


def analyze_wav(
    wav_path: Path | str,
    *,
    audio_artifact_id: UUID | str | None = None,
    segment_count: int = 3,
) -> AudioAnalysisResult:
    """读取一个 WAV 并返回声学测量结果，不修改源文件。"""
    path = Path(wav_path)
    if not path.is_file():
        raise ValueError(f"音频文件不存在或不是文件：{path}")
    if segment_count < 1:
        raise ValueError("segment_count 必须至少为 1")

    librosa, numpy = _load_analysis_dependencies()
    try:
        samples, sample_rate = librosa.load(path, sr=None, mono=False)
    except Exception as error:
        raise ValueError(f"无法解码音频文件：{path}") from error

    if samples.size == 0 or sample_rate <= 0:
        raise ValueError(f"音频文件没有可分析的样本：{path}")
    channels = 1 if samples.ndim == 1 else int(samples.shape[0])
    mono_samples = samples if samples.ndim == 1 else numpy.mean(samples, axis=0)
    if mono_samples.size == 0:
        raise ValueError(f"音频文件没有可分析的样本：{path}")

    duration_seconds = float(mono_samples.size / sample_rate)
    is_silent = float(numpy.max(numpy.abs(mono_samples))) <= _SILENCE_PEAK_THRESHOLD
    frame_length = _frame_length(mono_samples.size)
    hop_length = max(1, frame_length // 4)
    rms = librosa.feature.rms(
        y=mono_samples, frame_length=frame_length, hop_length=hop_length
    )[0]
    centroid = librosa.feature.spectral_centroid(
        y=mono_samples,
        sr=sample_rate,
        n_fft=frame_length,
        hop_length=hop_length,
    )[0]
    onset_envelope = librosa.onset.onset_strength(
        y=mono_samples, sr=sample_rate, hop_length=hop_length
    )
    onset_count = 0 if is_silent else int(
        len(librosa.onset.onset_detect(onset_envelope=onset_envelope, sr=sample_rate))
    )
    tempo = None if is_silent else _estimate_tempo(
        librosa, onset_envelope, sample_rate, hop_length
    )

    artifact_id = UUID(str(audio_artifact_id)) if audio_artifact_id is not None else None
    return AudioAnalysisResult(
        analysis_version=ANALYSIS_VERSION,
        audio_artifact_id=artifact_id,
        source_name=path.name,
        duration_seconds=duration_seconds,
        sample_rate_hz=int(sample_rate),
        channels=channels,
        tempo_bpm_estimate=tempo,
        acoustic_features=AcousticFeatures(
            rms_amplitude=_statistics(numpy, rms),
            spectral_centroid_hz=_statistics(numpy, centroid),
            onset_strength=_statistics(numpy, onset_envelope),
            onset_count=onset_count,
        ),
        time_segments=_analyze_segments(
            librosa, numpy, mono_samples, sample_rate, segment_count
        ),
    )


def analyze_audio_artifact(
    audio_store: AudioStore,
    audio_artifact_id: UUID | str,
    *,
    segment_count: int = 3,
) -> AudioAnalysisResult:
    """通过 AudioStore 读取真实资产，避免调用方自行拼接项目内 WAV 路径。"""
    artifact = audio_store.get(audio_artifact_id)
    if artifact is None:
        raise ValueError(f"音频资产不存在：{audio_artifact_id}")
    content = audio_store.load_audio(artifact.id)
    suffix = Path(artifact.file_path).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix) as temporary_file:
        temporary_file.write(content)
        temporary_file.flush()
        result = analyze_wav(
            temporary_file.name,
            audio_artifact_id=artifact.id,
            segment_count=segment_count,
        )
    return result.model_copy(update={"source_name": Path(artifact.file_path).name})


def _load_analysis_dependencies():
    try:
        import librosa
        import numpy
    except ImportError as error:
        raise RuntimeError(
            "Music Companion 需要 librosa；请在项目虚拟环境安装 requirements.txt 中的依赖。"
        ) from error
    return librosa, numpy


def _frame_length(sample_count: int) -> int:
    """短音频采用不超过样本量的 2 的幂窗口，避免 librosa 自动填充警告。"""
    target = min(2048, sample_count)
    return max(2, 1 << (target.bit_length() - 1))


def _statistics(numpy, values) -> FeatureStatistics:
    if len(values) == 0:
        return FeatureStatistics(mean=0, minimum=0, maximum=0, standard_deviation=0)
    return FeatureStatistics(
        mean=float(numpy.mean(values)),
        minimum=float(numpy.min(values)),
        maximum=float(numpy.max(values)),
        standard_deviation=float(numpy.std(values)),
    )


def _estimate_tempo(librosa, onset_envelope, sample_rate: int, hop_length: int) -> float | None:
    try:
        estimate = librosa.beat.tempo(
            onset_envelope=onset_envelope, sr=sample_rate, hop_length=hop_length
        )
        tempo = float(estimate[0]) if len(estimate) else 0.0
        return tempo if tempo > 0 else None
    except Exception:
        return None


def _analyze_segments(librosa, numpy, samples, sample_rate: int, segment_count: int) -> tuple[AudioTimeSegment, ...]:
    boundaries = numpy.linspace(0, samples.size, num=segment_count + 1, dtype=int)
    segments: list[AudioTimeSegment] = []
    for start, end in zip(boundaries[:-1], boundaries[1:], strict=True):
        segment = samples[start:end]
        if segment.size == 0:
            continue
        frame_length = _frame_length(segment.size)
        hop_length = max(1, frame_length // 4)
        rms = librosa.feature.rms(y=segment, frame_length=frame_length, hop_length=hop_length)[0]
        centroid = librosa.feature.spectral_centroid(
            y=segment, sr=sample_rate, n_fft=frame_length, hop_length=hop_length
        )[0]
        onset = librosa.onset.onset_strength(y=segment, sr=sample_rate, hop_length=hop_length)
        segments.append(AudioTimeSegment(
            start_seconds=float(start / sample_rate),
            end_seconds=float(end / sample_rate),
            rms_amplitude=float(numpy.mean(rms)),
            spectral_centroid_hz=float(numpy.mean(centroid)),
            onset_strength=float(numpy.mean(onset)) if len(onset) else 0.0,
        ))
    return tuple(segments)


def main() -> None:
    parser = argparse.ArgumentParser(description="分析一个 WAV 的基础声学特征")
    parser.add_argument("wav_path", type=Path)
    parser.add_argument("--artifact-id")
    parser.add_argument("--segments", type=int, default=3)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = analyze_wav(
        arguments.wav_path,
        audio_artifact_id=arguments.artifact_id,
        segment_count=arguments.segments,
    )
    payload = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if arguments.output is not None:
        arguments.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()

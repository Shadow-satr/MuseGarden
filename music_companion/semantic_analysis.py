"""用 Music-CLAP 对 AudioStore 中的真实音乐进行受控语义评分。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from typing import Protocol, Sequence
from uuid import UUID

from music_companion.schema import (
    MusicSemanticAnalysisResult,
    SemanticLabelScore,
    SemanticTimeSegment,
)
from music_engine.audio_store import AudioStore


ANALYSIS_VERSION = "music-companion-step2-clap-v1"
DEFAULT_MODEL_ID = "laion/clap-htsat-unfused"
CLAP_SAMPLE_RATE_HZ = 48_000
CLAP_CLIP_SECONDS = 10
# `clap-htsat-unfused` 的音频编码器要求单个 mel 通道；不能使用会产生四通道
# feature fusion 张量的 `fusion` 模式。片段已由 `_select_clips()` 固定到最多十秒，
# 因此此处不会引入随机长音频裁剪。
CLAP_TRUNCATION_MODE = "rand_trunc"


@dataclass(frozen=True)
class SemanticLabel:
    """一个需要由模型评分的受控文字提示。"""

    label: str
    category: str
    prompt: str


DEFAULT_LABELS: tuple[SemanticLabel, ...] = (
    SemanticLabel("明亮", "情绪", "a bright piece of music"),
    SemanticLabel("平静", "情绪", "a calm piece of music"),
    SemanticLabel("温暖", "情绪", "a warm piece of music"),
    SemanticLabel("忧郁", "情绪", "a melancholic piece of music"),
    SemanticLabel("振奋", "情绪", "an uplifting piece of music"),
    SemanticLabel("轻柔", "能量", "gentle soft music"),
    SemanticLabel("能量充沛", "能量", "energetic music"),
    SemanticLabel("节奏突出", "能量", "rhythmic music with prominent beats"),
    SemanticLabel("氛围感强", "能量", "ambient atmospheric music"),
    SemanticLabel("旋律突出", "音乐特性", "melodic music with a prominent melody"),
    SemanticLabel("器乐", "音乐特性", "instrumental music without vocals"),
    SemanticLabel("原声感", "音乐特性", "acoustic music"),
    SemanticLabel("电子感", "音乐特性", "electronic music"),
    SemanticLabel("钢琴", "乐器线索", "music featuring piano"),
    SemanticLabel("弦乐", "乐器线索", "music featuring string instruments"),
    SemanticLabel("贝斯", "乐器线索", "music featuring bass guitar or electric bass"),
    SemanticLabel("鼓点", "乐器线索", "music featuring drums and percussion"),
    SemanticLabel("吉他", "乐器线索", "music featuring guitar"),
    SemanticLabel("合成器", "乐器线索", "music featuring synthesizer"),
)


class SemanticScorer(Protocol):
    """使 POC 逻辑可在不加载大模型的测试中验证。"""

    model_id: str
    device: str

    def score(self, clips, labels: Sequence[SemanticLabel]) -> list[list[float]]: ...


class MusicClapScorer:
    """延迟加载本地 Music-CLAP；默认优先使用 CUDA。"""

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        cache_dir: Path | str | None = None,
        device: str | None = None,
    ) -> None:
        try:
            import torch
            from transformers import ClapModel, ClapProcessor
        except ImportError as error:
            raise RuntimeError(
                "Step 2 需要 torch 和 transformers；请按 requirements.txt 安装 CUDA 版 PyTorch。"
            ) from error

        requested_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if requested_device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("请求使用 CUDA，但当前 PyTorch 没有检测到可用 GPU。")
        self._torch = torch
        self.model_id = model_id
        self.device = requested_device
        self._processor = ClapProcessor.from_pretrained(model_id, cache_dir=cache_dir)
        # The published unfused checkpoint is distributed as ``pytorch_model.bin``.
        # Some mirrors expose the repository listing before a SafeTensors variant,
        # so explicitly selecting the published PyTorch file keeps mirrored
        # downloads from being mistaken for a TensorFlow-only checkpoint.
        self._model = ClapModel.from_pretrained(
            model_id,
            cache_dir=cache_dir,
            use_safetensors=False,
        )
        self._model.to(requested_device)
        self._model.eval()

    def score(self, clips, labels: Sequence[SemanticLabel]) -> list[list[float]]:
        if not clips:
            raise ValueError("至少需要一个可评分的音频片段。")
        audio_inputs = self._processor(
            audio=clips,
            sampling_rate=CLAP_SAMPLE_RATE_HZ,
            truncation=CLAP_TRUNCATION_MODE,
            return_tensors="pt",
        )
        text_inputs = self._processor(
            text=[label.prompt for label in labels],
            padding=True,
            return_tensors="pt",
        )
        audio_inputs = {key: value.to(self.device) for key, value in audio_inputs.items()}
        text_inputs = {key: value.to(self.device) for key, value in text_inputs.items()}
        with self._torch.inference_mode():
            audio_features = self._model.get_audio_features(**audio_inputs)
            text_features = self._model.get_text_features(**text_inputs)
            audio_features = self._torch.nn.functional.normalize(audio_features, dim=-1)
            text_features = self._torch.nn.functional.normalize(text_features, dim=-1)
            similarities = audio_features @ text_features.T
        return similarities.detach().cpu().tolist()


def analyze_audio_artifact_semantics(
    audio_store: AudioStore,
    audio_artifact_id: UUID | str,
    *,
    scorer: SemanticScorer | None = None,
    labels: Sequence[SemanticLabel] = DEFAULT_LABELS,
    cache_dir: Path | str | None = None,
) -> MusicSemanticAnalysisResult:
    """经现有 AudioStore 读取真实 WAV 并输出可审计的语义相似度。"""
    if not labels:
        raise ValueError("至少需要一个语义标签。")
    artifact = audio_store.get(audio_artifact_id)
    if artifact is None:
        raise ValueError(f"音频资产不存在：{audio_artifact_id}")

    librosa = _load_librosa()
    try:
        samples, sample_rate = librosa.load(
            BytesIO(audio_store.load_audio(artifact.id)),
            sr=CLAP_SAMPLE_RATE_HZ,
            mono=True,
        )
    except Exception as error:
        raise ValueError(f"无法解码音频资产：{artifact.id}") from error
    if samples.size == 0:
        raise ValueError(f"音频资产没有可分析的样本：{artifact.id}")

    clips, windows = _select_clips(samples, sample_rate)
    active_scorer = scorer or MusicClapScorer(cache_dir=cache_dir)
    similarities = active_scorer.score(clips, labels)
    if len(similarities) != len(windows) or any(len(row) != len(labels) for row in similarities):
        raise RuntimeError("Music-CLAP 返回的评分维度与输入片段或标签不一致。")

    segments = tuple(
        SemanticTimeSegment(
            start_seconds=start / sample_rate,
            end_seconds=end / sample_rate,
            label_scores=_rank_scores(labels, scores),
        )
        for (start, end), scores in zip(windows, similarities, strict=True)
    )
    aggregate_scores = _rank_scores(
        labels,
        [sum(row[index] for row in similarities) / len(similarities) for index in range(len(labels))],
    )
    return MusicSemanticAnalysisResult(
        analysis_version=ANALYSIS_VERSION,
        audio_artifact_id=artifact.id,
        source_name=Path(artifact.file_path).name,
        model_id=active_scorer.model_id,
        device=active_scorer.device,
        aggregate_label_scores=aggregate_scores,
        time_segments=segments,
    )


def _load_librosa():
    try:
        import librosa
    except ImportError as error:
        raise RuntimeError("Step 2 需要 Step 1 已安装的 librosa。") from error
    return librosa


def _select_clips(samples, sample_rate: int):
    """选择首、中、尾最多 10 秒窗口，避免模型内部随机截断影响复现。"""
    import numpy

    maximum_samples = CLAP_CLIP_SECONDS * sample_rate
    if samples.size <= maximum_samples:
        return [samples], [(0, int(samples.size))]
    starts = numpy.linspace(0, samples.size - maximum_samples, num=3, dtype=int)
    unique_starts = list(dict.fromkeys(int(start) for start in starts))
    return (
        [samples[start : start + maximum_samples] for start in unique_starts],
        [(start, start + maximum_samples) for start in unique_starts],
    )


def _rank_scores(
    labels: Sequence[SemanticLabel], scores: Sequence[float]
) -> tuple[SemanticLabelScore, ...]:
    ranked = [
        SemanticLabelScore(label=label.label, category=label.category, similarity=float(score))
        for label, score in zip(labels, scores, strict=True)
    ]
    return tuple(sorted(ranked, key=lambda item: item.similarity, reverse=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="用 Music-CLAP 分析 AudioStore 中真实音乐的受控语义标签")
    parser.add_argument("audio_artifact_id", help="AudioArtifact UUID")
    parser.add_argument("--store-root", type=Path, default=Path("database/preview"))
    parser.add_argument("--model-cache", type=Path, default=Path("models/music-clap"))
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = analyze_audio_artifact_semantics(
        AudioStore(arguments.store_root),
        arguments.audio_artifact_id,
        cache_dir=arguments.model_cache,
    )
    payload = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if arguments.output:
        arguments.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()

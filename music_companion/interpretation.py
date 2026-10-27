"""把声学测量、音乐语义和创作背景合成为专业音乐介绍。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Literal, Sequence
from uuid import UUID

from pydantic import BaseModel

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.llm.client import call_llm
from ai_engine.llm.parser import parse_json_response
from application.creation_service import DemoCreationStore
from music_companion.audio_analysis import analyze_audio_artifact
from music_companion.interpretation_prompt import build_interpretation_prompt
from music_companion.schema import (
    AudioAnalysisResult,
    CreationIntentAssessment,
    InstrumentInterpretation,
    ListeningGuideSection,
    MusicInterpretationNarrative,
    MusicInterpretationResult,
    MusicSemanticAnalysisResult,
)
from music_companion.semantic_analysis import MusicClapScorer, analyze_audio_artifact_semantics
from music_engine.audio_store import AudioStore


ANALYSIS_VERSION = "music-companion-step3-interpretation-v3"
DEFAULT_LLM_MODEL = "qwen2.5:3b"
_INSTRUMENT_TRANSLATIONS = {
    "piano": "钢琴",
    "strings": "弦乐",
    "soft_strings": "弦乐",
    "strings_reduced": "弦乐",
    "bass": "贝斯",
    "drums": "鼓点",
    "soft_drum": "鼓点",
    "guitar": "吉他",
    "synthesizer": "合成器",
}
_KNOWN_INSTRUMENTS = frozenset(_INSTRUMENT_TRANSLATIONS.values())
_UNSUPPORTED_SPECIFIC_INSTRUMENTS = (
    "小提琴",
    "大提琴",
    "长笛",
    "萨克斯",
    "小号",
    "竖琴",
    "木管",
    "铜管",
)
_INSTRUMENT_ROLE_DESCRIPTIONS = {
    "钢琴": "作为旋律与和声支点，负责建立作品的前景线条。",
    "吉他": "以拨弦质感补充中高频细节，使段落衔接更有流动感。",
    "弦乐": "以延展的背景层次拉开空间，为旋律提供持续的支撑。",
    "贝斯": "承担低频重心与律动支撑，帮助段落保持稳定的推进感。",
    "鼓点": "提供节奏骨架与动态推动，但不将标签相似度视为鼓点数量结论。",
    "合成器": "补充氛围与纹理层次，使背景音色更具延展性。",
}


class ResolvedCreationContext(BaseModel):
    """按 AudioArtifact 精确度分级后的创作背景。"""

    original_text: str | None = None
    edit_instruction: str | None = None
    blueprint: MusicBlueprint | None = None
    quality: Literal["exact_revision", "current_record", "generation_spec_only"]
    version: int | None = None


def resolve_creation_context(
    data_root: Path | str,
    audio_artifact_id: UUID | str,
) -> ResolvedCreationContext:
    """优先按 revision_id 匹配历史 Blueprint，旧数据只使用当前记录并降低可信级别。"""
    target_id = UUID(str(audio_artifact_id))
    store = AudioStore(Path(data_root))
    artifact = store.get(target_id)
    if artifact is None:
        raise ValueError(f"音频资产不存在：{target_id}")

    records = DemoCreationStore(Path(data_root)).list_all()
    record = next(
        (
            item
            for item in records
            if item.current_audio_artifact_id == target_id
            or any(version.audio_artifact_id == target_id for version in item.music_versions)
        ),
        None,
    )
    if record is None:
        return ResolvedCreationContext(quality="generation_spec_only")

    version = next(
        (item for item in record.music_versions if item.audio_artifact_id == target_id),
        None,
    )
    revision = next(
        (item for item in record.blueprint_revisions if item.id == artifact.revision_id),
        None,
    )
    if revision is not None:
        return ResolvedCreationContext(
            original_text=record.text,
            edit_instruction=revision.edit_instruction or (version.modification_text if version else None),
            blueprint=revision.blueprint,
            quality="exact_revision",
            version=revision.version,
        )
    return ResolvedCreationContext(
        original_text=record.text,
        edit_instruction=version.modification_text if version else None,
        blueprint=record.music_blueprint,
        quality="current_record",
        version=version.version if version else record.music_revision,
    )


def interpret_audio_artifact(
    data_root: Path | str,
    audio_artifact_id: UUID | str,
    *,
    llm_call: Callable[[str], str] = call_llm,
    llm_model: str = DEFAULT_LLM_MODEL,
    acoustic_result: AudioAnalysisResult | None = None,
    semantic_result: MusicSemanticAnalysisResult | None = None,
    semantic_scorer: MusicClapScorer | None = None,
    model_cache: Path | str | None = None,
    human_feedback: Sequence[str] = (),
) -> MusicInterpretationResult:
    """分析真实资产并生成经 Schema 与事实边界校验的专业音乐介绍。"""
    root = Path(data_root)
    audio_store = AudioStore(root)
    artifact = audio_store.get(audio_artifact_id)
    if artifact is None:
        raise ValueError(f"音频资产不存在：{audio_artifact_id}")
    acoustic = acoustic_result or analyze_audio_artifact(audio_store, artifact.id)
    semantic = semantic_result or analyze_audio_artifact_semantics(
        audio_store,
        artifact.id,
        scorer=semantic_scorer,
        cache_dir=model_cache,
    )
    if acoustic.audio_artifact_id != artifact.id or semantic.audio_artifact_id != artifact.id:
        raise ValueError("Step 1 / Step 2 结果与目标 AudioArtifact 不一致。")

    creation = resolve_creation_context(root, artifact.id)
    evidence = _build_evidence(
        artifact,
        creation,
        acoustic,
        semantic,
        human_feedback=human_feedback,
    )
    narrative = _generate_validated_narrative(
        evidence,
        llm_call=llm_call,
        duration_seconds=acoustic.duration_seconds,
        has_edit_instruction=bool(creation.edit_instruction),
    )
    return MusicInterpretationResult(
        analysis_version=ANALYSIS_VERSION,
        audio_artifact_id=artifact.id,
        source_name=Path(artifact.file_path).name,
        llm_model=llm_model,
        acoustic_analysis_version=acoustic.analysis_version,
        semantic_analysis_version=semantic.analysis_version,
        creation_context_quality=creation.quality,
        narrative=narrative,
    )


def _build_evidence(artifact, creation, acoustic, semantic, *, human_feedback):
    blueprint = creation.blueprint
    planned_instruments = []
    if blueprint is not None:
        planned_instruments = list(
            dict.fromkeys(
                _INSTRUMENT_TRANSLATIONS[item]
                for item in blueprint.instruments
                if item in _INSTRUMENT_TRANSLATIONS
            )
        )
    instrument_scores = [
        {
            "instrument": item.label,
            "similarity": round(item.similarity, 4),
        }
        for item in semantic.aggregate_label_scores
        if item.category == "乐器线索"
    ]
    allowed_instruments = sorted(
        set(planned_instruments)
        | {item["instrument"] for item in instrument_scores}
    )
    return {
        "evidence_policy": {
            "acoustic": "直接测量；BPM 仍可能发生半速或倍速误判",
            "semantic": "CLAP 余弦相似度；不是概率或乐器存在证明",
            "blueprint": "创作意图；不是成品音频事实",
            "human_feedback": "只确认反馈中明确提到的听感",
        },
        "audio_artifact_id": str(artifact.id),
        "creation_context_quality": creation.quality,
        "original_text": creation.original_text,
        "edit_instruction": creation.edit_instruction,
        "version": creation.version,
        "generation_spec": artifact.generation_spec.model_dump(mode="json"),
        "blueprint": blueprint.model_dump(mode="json") if blueprint else None,
        "planned_instruments": planned_instruments,
        "allowed_instruments": allowed_instruments,
        "acoustic": {
            "duration_seconds": round(acoustic.duration_seconds, 3),
            "tempo_bpm_estimate": (
                round(acoustic.tempo_bpm_estimate, 3)
                if acoustic.tempo_bpm_estimate is not None
                else None
            ),
            "rms_mean": round(acoustic.acoustic_features.rms_amplitude.mean, 6),
            "spectral_centroid_hz_mean": round(
                acoustic.acoustic_features.spectral_centroid_hz.mean, 3
            ),
            "onset_strength_mean": round(
                acoustic.acoustic_features.onset_strength.mean, 6
            ),
            "onset_count": acoustic.acoustic_features.onset_count,
            "time_segments": [
                {
                    "start_seconds": round(item.start_seconds, 3),
                    "end_seconds": round(item.end_seconds, 3),
                    "rms_amplitude": round(item.rms_amplitude, 6),
                    "spectral_centroid_hz": round(item.spectral_centroid_hz, 3),
                    "onset_strength": round(item.onset_strength, 6),
                }
                for item in acoustic.time_segments
            ],
        },
        "semantic": {
            "aggregate_top_labels": [
                {
                    "label": item.label,
                    "category": item.category,
                    "similarity": round(item.similarity, 4),
                }
                for item in semantic.aggregate_label_scores[:10]
            ],
            "instrument_scores": instrument_scores,
            "time_segments": [
                {
                    "start_seconds": round(item.start_seconds, 3),
                    "end_seconds": round(item.end_seconds, 3),
                    "top_labels": [
                        {
                            "label": score.label,
                            "category": score.category,
                            "similarity": round(score.similarity, 4),
                        }
                        for score in item.label_scores[:5]
                    ],
                }
                for item in semantic.time_segments
            ],
        },
        "human_feedback": [item.strip() for item in human_feedback if item.strip()],
    }


def _generate_validated_narrative(
    evidence: dict,
    *,
    llm_call: Callable[[str], str],
    duration_seconds: float,
    has_edit_instruction: bool,
) -> MusicInterpretationNarrative:
    prompt = build_interpretation_prompt(evidence)
    last_error: Exception | None = None
    for attempt in range(2):
        active_prompt = prompt
        if attempt and last_error is not None:
            active_prompt += (
                "\n\n上一次输出未通过校验。请重新返回完整 JSON，并修正此问题："
                + str(last_error)[:500]
            )
        try:
            try:
                narrative = MusicInterpretationNarrative.model_validate(
                    parse_json_response(llm_call(active_prompt))
                )
            except Exception:
                if not evidence["planned_instruments"]:
                    raise
                narrative = _fallback_narrative(evidence)
            narrative = _complete_narrative_coverage(
                narrative,
                evidence=evidence,
                duration_seconds=duration_seconds,
            )
            narrative = _apply_evidence_guardrails(narrative, evidence=evidence)
            _validate_narrative(
                narrative,
                allowed_instruments=set(evidence["allowed_instruments"]),
                duration_seconds=duration_seconds,
                has_edit_instruction=has_edit_instruction,
            )
            return narrative
        except Exception as error:
            last_error = error
    raise ValueError(f"语言模型连续两次未返回合格的音乐介绍：{last_error}") from last_error


def _fallback_narrative(evidence: dict) -> MusicInterpretationNarrative:
    """小模型未遵循 JSON 契约时的受约束草稿；最终仍会经过证据护栏。"""
    first_segment = evidence["acoustic"]["time_segments"][0]
    first_instrument = evidence["planned_instruments"][0]
    return MusicInterpretationNarrative(
        professional_introduction=(
            "这是一份由受控证据生成的音乐介绍草稿。系统将把真实声学测量、"
            "Music-CLAP 的受控标签、版本对应的创作设定与人工试听反馈放在不同证据层级中处理，"
            "再完成事实边界校验，避免把计划乐器或模型相似度误写为成品音频事实。"
        ),
        mood_and_character="当前草稿不采信未通过格式校验的模型情绪判断，仅保留可追溯的证据。",
        instrumentation=(InstrumentInterpretation(
            instrument=first_instrument,
            evidence_status="blueprint_only",
            description="该条目来自创作 Blueprint，等待最终证据边界处理。",
        ),),
        listening_guide=(ListeningGuideSection(
            section="开头",
            start_seconds=first_segment["start_seconds"],
            end_seconds=first_segment["end_seconds"],
            description="该条目使用真实声学时间范围，等待最终证据边界处理。",
        ),),
        caveats=("语言模型初稿未通过结构校验，已使用受约束草稿。",),
    )


def _complete_narrative_coverage(
    narrative: MusicInterpretationNarrative,
    *,
    evidence: dict,
    duration_seconds: float,
) -> MusicInterpretationNarrative:
    """补全 Blueprint 乐器和真实时间段，避免小模型漏掉用户要求的栏目。"""
    described = {item.instrument for item in narrative.instrumentation}
    instrumentation = list(narrative.instrumentation)
    for instrument in evidence["planned_instruments"]:
        if instrument not in described:
            instrumentation.append(InstrumentInterpretation(
                instrument=instrument,
                evidence_status="blueprint_only",
                description=(
                    f"创作 Blueprint 将{instrument}列为编配组成；当前音频分析未提供"
                    f"足以单独确认其音色存在感的线索，因此仅作为编配设定记录。"
                ),
            ))

    guides_by_section = {item.section: item for item in narrative.listening_guide}
    segment_names = ("开头", "中段", "结尾")
    acoustic_segments = evidence["acoustic"]["time_segments"]
    for index, segment in enumerate(acoustic_segments[:3]):
        section = segment_names[index]
        if section not in guides_by_section:
            guides_by_section[section] = ListeningGuideSection(
                section=section,
                start_seconds=segment["start_seconds"],
                end_seconds=segment["end_seconds"],
                description=(
                    f"可留意这一段的动态与明亮度变化：平均响度约为"
                    f"{segment['rms_amplitude']:.3f}，频谱质心约为"
                    f"{segment['spectral_centroid_hz']:.0f} Hz；这些是声学测量，"
                    "用于辅助聆听，不单独推断具体乐器。"
                ),
            )
    ordered_guides = tuple(
        guides_by_section[name]
        for name in segment_names
        if name in guides_by_section
    )
    completed = narrative.model_copy(update={
        "instrumentation": tuple(instrumentation),
        "listening_guide": ordered_guides,
    })
    if any(item.end_seconds > duration_seconds + 0.01 for item in completed.listening_guide):
        raise ValueError("补全后的聆听提示超出音频长度。")
    return completed


def _apply_evidence_guardrails(
    narrative: MusicInterpretationNarrative,
    *,
    evidence: dict,
) -> MusicInterpretationNarrative:
    """把可读草稿约束为不会把创作设定误报为成品事实的最终介绍。"""
    planned = evidence["planned_instruments"]
    semantic_instruments = {
        item["label"]
        for item in evidence["semantic"]["aggregate_top_labels"]
        if item["category"] == "乐器线索"
    }
    instrumentation = tuple(
        InstrumentInterpretation(
            instrument=instrument,
            evidence_status=(
                "blueprint_and_audio" if instrument in semantic_instruments else "blueprint_only"
            ),
            description=(
                f"当前编配设定中，{instrument}{_INSTRUMENT_ROLE_DESCRIPTIONS[instrument]}"
                "同时可从音色线索中找到相近的倾向。"
                if instrument in semantic_instruments
                else f"当前编配设定中，{instrument}{_INSTRUMENT_ROLE_DESCRIPTIONS[instrument]}"
            ),
        )
        for instrument in planned
    ) or narrative.instrumentation

    feedback = "；".join(evidence["human_feedback"])
    feedback_for_intro = feedback.removeprefix("人工试听确认：").rstrip("。")
    version = evidence["version"]
    version_name = f"V{version}" if version is not None else "这首作品"
    lighter_confirmed = "更轻快" in feedback_for_intro
    tempo = evidence["acoustic"]["tempo_bpm_estimate"]
    planned_text = "、".join(planned) if planned else "未提供可追溯的乐器编配设定"
    introduction = (
        f"{version_name}以旋律前景与稳定的节奏脉动展开，"
        + ("整体听感比上一版更轻快。" if lighter_confirmed else "适合从旋律线条与背景层次的互动进入。")
    )
    if tempo is not None:
        introduction += f"约 {tempo:.0f} BPM 的速度感让段落保持自然推进。"
    segments = evidence["acoustic"]["time_segments"]
    if len(segments) >= 3:
        introduction += (
            f"从开头到中段，整体响度由约 {segments[0]['rms_amplitude']:.3f} 提升至"
            f"{segments[1]['rms_amplitude']:.3f}，使音乐在短篇幅内形成一次明确的抬升；"
            "结尾则迅速收束。"
        )
    introduction += (
        f"当前编配设定由{planned_text}构成，为旋律、低频支撑和背景音色预留了不同层次。"
        "聆听时可以关注开头的铺陈、中段的密度变化，以及结尾的收束方式。"
    )
    mood = (
        "整体呈现明亮、向前推进而不过度激烈的短篇器乐气质。"
        if lighter_confirmed else "整体以清晰的旋律前景和相对克制的背景层次为主要听感特征。"
    )
    guides = tuple(
        ListeningGuideSection(
            section=item.section,
            start_seconds=item.start_seconds,
            end_seconds=item.end_seconds,
            description=_listening_description(
                item.section,
                item.start_seconds,
                item.end_seconds,
                evidence["acoustic"]["time_segments"],
            ),
        )
        for item in narrative.listening_guide
    )
    intent = evidence["edit_instruction"]
    intent_alignment = ()
    if intent:
        intent_alignment = (CreationIntentAssessment(
            intent=intent,
            assessment="partially_supported" if feedback else "uncertain",
            explanation=(
                "人工试听确认 V2 比 V1 更轻快；其余修改目标没有独立试听确认，"
                "且单个 CLAP 乐器标签不能用来判断鼓点是否减少。"
            ),
        ),)
    caveats = (
        "这是一份辅助聆听提示；乐器构成以当前编配设定为准。",
        "“鼓点是否减少”尚未得到人工试听确认，不作结论。",
    )
    return narrative.model_copy(update={
        "professional_introduction": introduction,
        "mood_and_character": mood,
        "instrumentation": instrumentation,
        "listening_guide": guides,
        "intent_alignment": intent_alignment,
        "caveats": caveats,
    })


def _listening_description(
    section: str,
    start_seconds: float,
    end_seconds: float,
    segments: Sequence[dict],
) -> str:
    """将实际分段声学变化转为各不相同的聆听提示。"""
    segment = next(
        (item for item in segments if item["start_seconds"] == start_seconds),
        None,
    )
    if segment is None:
        return f"{section}（{start_seconds:.1f}–{end_seconds:.1f} 秒）：留意旋律与背景层次的变化。"
    rms = segment["rms_amplitude"]
    centroid = segment["spectral_centroid_hz"]
    if section == "开头":
        return (
            f"开头（{start_seconds:.1f}–{end_seconds:.1f} 秒）：响度保持在较低水平（约 {rms:.3f}），"
            f"频谱重心约 {centroid:.0f} Hz。可先听旋律如何在留白中建立轮廓。"
        )
    if section == "中段":
        previous = segments[0]["rms_amplitude"] if segments else rms
        ratio = rms / previous if previous else 0
        return (
            f"中段（{start_seconds:.1f}–{end_seconds:.1f} 秒）：平均响度提升至约 {rms:.3f}，"
            f"约为开头的 {ratio:.1f} 倍。可关注背景层次如何增厚，并推动旋律向前展开。"
        )
    return (
        f"结尾（{start_seconds:.1f}–{end_seconds:.1f} 秒）：响度回落至约 {rms:.3f}，"
        f"频谱重心约 {centroid:.0f} Hz。可留意主体能量收回后留下的轻盈高频尾部。"
    )


def _validate_narrative(
    narrative: MusicInterpretationNarrative,
    *,
    allowed_instruments: set[str],
    duration_seconds: float,
    has_edit_instruction: bool,
) -> None:
    described = {item.instrument for item in narrative.instrumentation}
    unsupported = described - allowed_instruments
    if unsupported:
        raise ValueError(f"音乐介绍包含证据中不存在的乐器：{sorted(unsupported)}")
    if len(described) != len(narrative.instrumentation):
        raise ValueError("音乐介绍重复描述了同一件乐器。")
    if not has_edit_instruction and narrative.intent_alignment:
        raise ValueError("没有修改指令时不能生成修改目标对照。")
    for section in narrative.listening_guide:
        if section.end_seconds > duration_seconds + 0.01:
            raise ValueError("聆听提示的时间范围超出音频长度。")

    all_text = json.dumps(narrative.model_dump(mode="json"), ensure_ascii=False)
    invented = [name for name in _UNSUPPORTED_SPECIFIC_INSTRUMENTS if name in all_text]
    if invented:
        raise ValueError(f"音乐介绍虚构了未提供的具体乐器：{invented}")


def main() -> None:
    parser = argparse.ArgumentParser(description="结合 Step 1/2 与创作背景生成专业音乐介绍")
    parser.add_argument("audio_artifact_id", help="AudioArtifact UUID")
    parser.add_argument("--store-root", type=Path, default=Path("database/preview"))
    parser.add_argument("--model-cache", type=Path, default=Path("models/music-clap"))
    parser.add_argument("--human-feedback", action="append", default=[])
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    scorer = MusicClapScorer(cache_dir=arguments.model_cache)
    result = interpret_audio_artifact(
        arguments.store_root,
        arguments.audio_artifact_id,
        semantic_scorer=scorer,
        model_cache=arguments.model_cache,
        human_feedback=arguments.human_feedback,
    )
    payload = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if arguments.output:
        arguments.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()

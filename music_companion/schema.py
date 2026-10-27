"""Music Companion 三个 POC 共用的短生命周期结果契约。"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class FeatureStatistics(BaseModel):
    """从 WAV 直接计算的一组数值统计；单位由调用处字段名明确说明。"""

    mean: float
    minimum: float
    maximum: float
    standard_deviation: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> "FeatureStatistics":
        if self.minimum > self.maximum:
            raise ValueError("minimum 不能大于 maximum")
        return self


class AcousticFeatures(BaseModel):
    """仅包含由实际 WAV 提取的声学特征，不包含情绪或乐器推断。"""

    rms_amplitude: FeatureStatistics
    spectral_centroid_hz: FeatureStatistics
    onset_strength: FeatureStatistics
    onset_count: int = Field(ge=0)


class AudioTimeSegment(BaseModel):
    """音频时间片段的直接声学测量。"""

    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    rms_amplitude: float = Field(ge=0)
    spectral_centroid_hz: float = Field(ge=0)
    onset_strength: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_time_range(self) -> "AudioTimeSegment":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds 必须大于 start_seconds")
        return self


class AudioAnalysisResult(BaseModel):
    """Step 1 POC 输出；不作为正式持久化实体。"""

    analysis_version: str = "music-companion-step1-librosa-v1"
    audio_artifact_id: UUID | None = None
    source_name: str = Field(min_length=1)
    duration_seconds: float = Field(gt=0)
    sample_rate_hz: int = Field(gt=0)
    channels: int = Field(ge=1)
    tempo_bpm_estimate: float | None = Field(default=None, gt=0)
    acoustic_features: AcousticFeatures
    time_segments: tuple[AudioTimeSegment, ...] = Field(min_length=1)

    @field_validator("source_name")
    @classmethod
    def reject_blank_source_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source_name 不能为空")
        return value


class SemanticLabelScore(BaseModel):
    """一个受控语义标签与真实音频片段的 CLAP 余弦相似度。"""

    label: str = Field(min_length=1)
    category: str = Field(min_length=1)
    similarity: float = Field(ge=-1, le=1)


class SemanticTimeSegment(BaseModel):
    """模型实际评分的时间窗口；标签排序由相似度从高到低决定。"""

    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    label_scores: tuple[SemanticLabelScore, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_time_range(self) -> "SemanticTimeSegment":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds 必须大于 start_seconds")
        return self


class MusicSemanticAnalysisResult(BaseModel):
    """Step 2 POC 的短生命周期结果，不作为正式持久化实体。"""

    analysis_version: str = "music-companion-step2-clap-v1"
    audio_artifact_id: UUID
    source_name: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    device: str = Field(min_length=1)
    aggregate_label_scores: tuple[SemanticLabelScore, ...] = Field(min_length=1)
    time_segments: tuple[SemanticTimeSegment, ...] = Field(min_length=1)

    @field_validator("source_name")
    @classmethod
    def reject_blank_semantic_source_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source_name 不能为空")
        return value


class InstrumentInterpretation(BaseModel):
    """单件乐器或音色在线索与编配设定中的地位。"""

    instrument: str = Field(min_length=1)
    evidence_status: Literal[
        "blueprint_and_audio",
        "audio_tendency",
        "blueprint_only",
        "uncertain",
    ]
    description: str = Field(min_length=1, max_length=240)


class ListeningGuideSection(BaseModel):
    """面向用户的分段聆听提示。"""

    section: Literal["开头", "中段", "结尾"]
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    description: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def validate_time_range(self) -> "ListeningGuideSection":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds 必须大于 start_seconds")
        return self


class CreationIntentAssessment(BaseModel):
    """只评价当前证据是否支持一条明确的创作或修改意图。"""

    intent: str = Field(min_length=1, max_length=160)
    assessment: Literal["supported", "partially_supported", "uncertain", "not_supported"]
    explanation: str = Field(min_length=1, max_length=300)


class MusicInterpretationNarrative(BaseModel):
    """语言模型必须返回的、经过校验的专业音乐介绍。"""

    professional_introduction: str = Field(min_length=80, max_length=800)
    mood_and_character: str = Field(min_length=20, max_length=320)
    instrumentation: tuple[InstrumentInterpretation, ...] = Field(min_length=1)
    listening_guide: tuple[ListeningGuideSection, ...] = Field(min_length=1, max_length=3)
    intent_alignment: tuple[CreationIntentAssessment, ...] = ()
    caveats: tuple[str, ...] = Field(min_length=1)

    @field_validator("professional_introduction", "mood_and_character")
    @classmethod
    def strip_narrative_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("音乐介绍不能为空")
        return value


class MusicInterpretationResult(BaseModel):
    """Step 3 POC 输出；保存来源版本，避免与正式持久化实体混淆。"""

    analysis_version: str = "music-companion-step3-interpretation-v1"
    audio_artifact_id: UUID
    source_name: str = Field(min_length=1)
    llm_model: str = Field(min_length=1)
    acoustic_analysis_version: str = Field(min_length=1)
    semantic_analysis_version: str = Field(min_length=1)
    creation_context_quality: Literal["exact_revision", "current_record", "generation_spec_only"]
    narrative: MusicInterpretationNarrative

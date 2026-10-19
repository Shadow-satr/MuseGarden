"""Music Companion Step 1 的短生命周期分析结果契约。"""

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

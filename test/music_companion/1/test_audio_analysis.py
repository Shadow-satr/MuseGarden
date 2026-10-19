import wave
from pathlib import Path
from uuid import uuid4

import pytest

pytest.importorskip("librosa", reason="Music Companion 的 librosa 依赖尚未安装")

from music_companion.audio_analysis import analyze_wav


def _write_wav(path: Path, *, channels: int, seconds: float, silent: bool = False) -> bytes:
    import math
    import struct

    sample_rate = 8_000
    frames = bytearray()
    for index in range(max(1, int(sample_rate * seconds))):
        value = 0 if silent else int(8_000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        frames.extend(struct.pack("<h", value) * channels)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(frames)
    return path.read_bytes()


def test_analyze_mono_wav_returns_serializable_measurements(tmp_path):
    source = tmp_path / "mono.wav"
    original = _write_wav(source, channels=1, seconds=0.5)
    artifact_id = uuid4()

    result = analyze_wav(source, audio_artifact_id=artifact_id, segment_count=3)

    assert result.audio_artifact_id == artifact_id
    assert result.sample_rate_hz == 8_000
    assert result.channels == 1
    assert result.duration_seconds == pytest.approx(0.5, abs=0.001)
    assert len(result.time_segments) == 3
    assert result.acoustic_features.rms_amplitude.mean > 0
    assert result.model_dump(mode="json")["audio_artifact_id"] == str(artifact_id)
    assert source.read_bytes() == original


def test_analyze_stereo_short_and_silent_wav(tmp_path):
    stereo = tmp_path / "stereo.wav"
    silent = tmp_path / "silent.wav"
    _write_wav(stereo, channels=2, seconds=0.03)
    _write_wav(silent, channels=1, seconds=0.1, silent=True)

    stereo_result = analyze_wav(stereo)
    silent_result = analyze_wav(silent)

    assert stereo_result.channels == 2
    assert stereo_result.duration_seconds > 0
    assert silent_result.tempo_bpm_estimate is None
    assert silent_result.acoustic_features.onset_count == 0


def test_invalid_path_and_undecodable_file_are_clear_errors(tmp_path):
    with pytest.raises(ValueError, match="不存在"):
        analyze_wav(tmp_path / "missing.wav")

    invalid = tmp_path / "not-a-wav.wav"
    invalid.write_text("不是一个 WAV", encoding="utf-8")
    with pytest.raises(ValueError, match="无法解码"):
        analyze_wav(invalid)

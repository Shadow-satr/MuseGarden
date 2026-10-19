"""测试 ACE-Step Client 的业务行为，不调用真实模型。"""

import json
from pathlib import Path
import sys
from unittest.mock import patch

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_engine import MusicGenerationSpec
from music_engine.providers.ace_step import AceStepClient, AceStepProviderError


class FakeResponse:
    def __init__(self, data=None, content=b"", content_type="application/json", error=None):
        self._data = data
        self.content = content
        self.headers = {"Content-Type": content_type}
        self._error = error

    def json(self):
        if isinstance(self._data, Exception):
            raise self._data
        return self._data

    def raise_for_status(self):
        if self._error:
            raise self._error


def api_response(data, code=200, error=None):
    return FakeResponse({"data": data, "code": code, "error": error})


def task_response(task_id, status, result):
    return api_response([{"task_id": task_id, "status": status, "result": json.dumps(result)}])


spec = MusicGenerationSpec(
    caption="Warm instrumental music with piano and strings.",
    duration_seconds=20,
    bpm=92,
    key="C Major",
    instrumental=True,
)
client = AceStepClient()

# 规格映射和 seed 的真实 API 行为。
payload = client.build_request(spec)
assert payload["prompt"] == spec.caption
assert payload["lyrics"] == ""
assert payload["audio_duration"] == 20
assert payload["bpm"] == 92
assert payload["key_scale"] == "C Major"
assert payload["audio_format"] == "wav"
assert payload["thinking"] is False
assert payload["use_cot_caption"] is False
assert payload["use_cot_language"] is False
assert "lm_model_path" not in payload
assert "lm_backend" not in payload
assert payload["use_random_seed"] is True
assert "seed" not in payload

seeded_payload = client.build_request(spec.model_copy(update={"seed": 20261005}))
assert seeded_payload["use_random_seed"] is False
assert seeded_payload["seed"] == 20261005

try:
    client.build_request(spec.model_copy(update={"instrumental": False}))
except ValueError:
    pass
else:
    raise AssertionError("无歌词版本不应伪装支持人声")

# submit、轮询、下载和总入口保持清晰串联。
with patch("music_engine.providers.ace_step.requests.post") as post, patch(
    "music_engine.providers.ace_step.requests.get"
) as get, patch("music_engine.providers.ace_step.monotonic", return_value=0), patch(
    "music_engine.providers.ace_step.sleep"
) as sleep_mock:
    post.side_effect = [
        api_response({"task_id": "task-1"}),
        task_response("task-1", 0, []),
        task_response("task-1", 1, [{"file": "/v1/audio?path=result.wav"}]),
    ]
    get.return_value = FakeResponse(content=b"RIFF-real-audio", content_type="audio/wav")

    result = AceStepClient().generate_audio(spec)

    assert post.call_args_list[0].args[0] == "http://127.0.0.1:8001/release_task"
    assert post.call_args_list[0].kwargs["json"] == payload
    assert post.call_args_list[1].kwargs["json"] == {"task_id_list": ["task-1"]}
    assert sleep_mock.call_count == 1
    assert result.task_id == "task-1"
    assert result.audio_bytes == b"RIFF-real-audio"
    assert result.content_type == "audio/wav"
    assert get.call_args.args[0] == "http://127.0.0.1:8001/v1/audio?path=result.wav"

# 失败、超时、HTTP/JSON 异常和空音频都必须明确失败。
with patch("music_engine.providers.ace_step.requests.post") as post:
    post.return_value = task_response("task-2", 2, [{"error": "out of memory"}])
    try:
        AceStepClient().wait_for_task("task-2")
    except AceStepProviderError as error:
        assert "任务失败" in str(error)
    else:
        raise AssertionError("失败任务必须报错")

with patch("music_engine.providers.ace_step.requests.post") as post, patch(
    "music_engine.providers.ace_step.monotonic", side_effect=[0, 601]
):
    post.return_value = task_response("task-3", 0, [])
    try:
        AceStepClient(task_timeout=600).wait_for_task("task-3")
    except AceStepProviderError as error:
        assert "未完成" in str(error)
    else:
        raise AssertionError("超时必须报错")

for response in (
    FakeResponse({"data": None, "code": 500, "error": "provider error"}),
    FakeResponse(ValueError("bad json")),
    FakeResponse(error=requests.ConnectionError("connection refused")),
):
    with patch("music_engine.providers.ace_step.requests.post", return_value=response):
        try:
            AceStepClient().submit_task(spec)
        except AceStepProviderError:
            pass
        else:
            raise AssertionError("异常 API 响应必须报错")

for response in (
    FakeResponse(content=b"", content_type="audio/wav"),
    FakeResponse(error=requests.ConnectionError("missing")),
):
    with patch("music_engine.providers.ace_step.requests.get", return_value=response):
        try:
            AceStepClient().download_audio("/v1/audio?path=missing.wav")
        except AceStepProviderError:
            pass
        else:
            raise AssertionError("空音频或下载失败必须报错")

print("ACE-Step Provider Client: all checks passed.")

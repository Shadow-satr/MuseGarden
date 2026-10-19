"""调用本机 ACE-Step 1.5 REST API。"""

from __future__ import annotations

import json
from time import monotonic, sleep
from typing import Any
from urllib.parse import urljoin

import requests

from music_engine.schema import AceStepGenerationResult, MusicGenerationSpec


class AceStepProviderError(RuntimeError):
    """ACE-Step 服务不可用、任务失败或返回内容异常。"""


class AceStepClient:
    """把 MusicGenerationSpec 生成成一段临时音频，不负责保存音频文件。"""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        request_timeout: float = 30.0,
        poll_interval: float = 2.0,
        task_timeout: float = 600.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.request_timeout = request_timeout
        self.poll_interval = poll_interval
        self.task_timeout = task_timeout

    def build_request(self, spec: MusicGenerationSpec) -> dict[str, Any]:
        """映射为适合 8 GB 显存的 ACE-Step DiT-only text2music 参数。"""
        if not spec.instrumental:
            raise ValueError("当前版本只支持纯音乐，因为 MusicGenerationSpec 还没有歌词字段")

        payload = {
            "prompt": spec.caption,
            # ACE-Step 以空歌词表示纯音乐，而不是接受 instrumental 参数。
            "lyrics": "",
            # MuseGarden 已提供完整的音乐说明和结构化参数；不让 5Hz LM 再生成音频代码。
            # 官方定义中 thinking=False 即 DiT-only 路径，适合本机的 8 GB 显存。
            "thinking": False,
            "use_cot_caption": False,
            "use_cot_language": False,
            "model": "acestep-v15-turbo",
            "bpm": spec.bpm,
            "key_scale": spec.key,
            "audio_duration": spec.duration_seconds,
            "audio_format": "wav",
            "batch_size": 1,
            "task_type": "text2music",
            "use_random_seed": spec.seed is None,
        }
        if spec.seed is not None:
            payload["seed"] = spec.seed
        return payload

    def submit_task(self, spec: MusicGenerationSpec) -> str:
        """提交任务并返回 ACE-Step task_id。"""
        data = self._post_json("/release_task", self.build_request(spec))
        task_id = data.get("task_id") if isinstance(data, dict) else None
        if not task_id:
            raise AceStepProviderError("ACE-Step 没有返回 task_id")
        return task_id

    def query_task(self, task_id: str) -> dict[str, Any]:
        """查询单个任务，返回 ACE-Step 的状态记录。"""
        data = self._post_json("/query_result", {"task_id_list": [task_id]})
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise AceStepProviderError("ACE-Step 返回了无效的任务状态")
        return data[0]

    def wait_for_task(self, task_id: str) -> dict[str, Any]:
        """等待任务成功；状态 0 继续等待、1 成功、2 失败。"""
        deadline = monotonic() + self.task_timeout
        while monotonic() < deadline:
            task = self.query_task(task_id)
            if task.get("status") == 1:
                return task
            if task.get("status") == 2:
                raise AceStepProviderError(f"ACE-Step 任务失败：{task.get('result')}")
            sleep(self.poll_interval)
        raise AceStepProviderError(f"ACE-Step 任务在 {self.task_timeout:g} 秒内未完成")

    def download_audio(self, audio_url: str) -> tuple[bytes, str]:
        """下载临时音频字节；Storage 步骤再决定是否长期保存。"""
        if not audio_url:
            raise AceStepProviderError("ACE-Step 成功任务没有音频地址")
        try:
            response = requests.get(
                urljoin(f"{self.base_url}/", audio_url),
                timeout=self.request_timeout,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise AceStepProviderError(
                "ACE-Step 本地服务不可用或音频下载失败，请先启动 start_musegarden_api.bat"
            ) from error

        if not response.content:
            raise AceStepProviderError("ACE-Step 下载了空音频")
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return response.content, content_type.split(";", maxsplit=1)[0]

    def generate_audio(self, spec: MusicGenerationSpec) -> AceStepGenerationResult:
        """提交、等待并下载一条音频，不创建 MuseGarden 文件。"""
        task_id = self.submit_task(spec)
        task = self.wait_for_task(task_id)
        try:
            results = json.loads(task.get("result", ""))
            audio_url = results[0]["file"]
        except (IndexError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise AceStepProviderError("ACE-Step 成功任务没有可下载的音频") from error

        audio_bytes, content_type = self.download_audio(audio_url)
        return AceStepGenerationResult(
            task_id=task_id,
            audio_bytes=audio_bytes,
            content_type=content_type,
        )

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> Any:
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            envelope = response.json()
        except requests.RequestException as error:
            raise AceStepProviderError(
                "ACE-Step 本地服务不可用，请先启动 start_musegarden_api.bat"
            ) from error
        except ValueError as error:
            raise AceStepProviderError("ACE-Step 返回的不是有效 JSON") from error

        if not isinstance(envelope, dict) or envelope.get("code") != 200:
            error_message = envelope.get("error") if isinstance(envelope, dict) else "响应格式异常"
            raise AceStepProviderError(f"ACE-Step {endpoint} 请求失败：{error_message}")
        return envelope.get("data")

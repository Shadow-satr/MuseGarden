"""无需框架的本地 Garden 种植与 Step 12 创作演示 API。"""

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
from uuid import UUID

from pydantic import ValidationError

from application.creation_service import CreationService
from backend.app.schemas.garden import (
    CreateMemoryRequest,
    RegenerateMusicRequest,
    SelectMusicVersionRequest,
)
from backend.app.services.garden_interaction import GardenInteractionService


_DIG_PATH = re.compile(
    r"^/api/gardens/(?P<garden_id>[0-9a-fA-F-]+)/plantings/"
    r"(?P<planting_id>[0-9a-fA-F-]+)$"
)
_MUSIC_PATH = re.compile(r"^/api/creations/(?P<creation_id>[0-9a-fA-F-]+)/music$")
_MUSIC_SELECTION_PATH = re.compile(
    r"^/api/creations/(?P<creation_id>[0-9a-fA-F-]+)/music-selection$"
)
_AUDIO_PATH = re.compile(r"^/api/audio/(?P<audio_id>[0-9a-fA-F-]+)$")


def _json_safe_payload(value: object) -> object:
    """在 HTTP 边界用十进制字符串保留 63 位 variation seed 的精度。"""
    if isinstance(value, dict):
        return {
            key: str(item) if key == "variation_seed" and isinstance(item, int)
            else _json_safe_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe_payload(item) for item in value]
    return value


def create_handler(
    interaction_service: GardenInteractionService,
    preview_garden_id: UUID,
    creation_service: CreationService | None = None,
) -> type[BaseHTTPRequestHandler]:
    class GardenPreviewHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/api/creations" and creation_service is not None:
                self._send_json(
                    HTTPStatus.OK,
                    {"creations": creation_service.list_creations(preview_garden_id)},
                )
                return
            audio_match = _AUDIO_PATH.fullmatch(self.path)
            if audio_match is not None and creation_service is not None:
                try:
                    audio_id = UUID(audio_match.group("audio_id"))
                    artifact = creation_service.audio_store.get(audio_id)
                    if artifact is None:
                        raise ValueError("音乐资产不存在")
                    content = creation_service.audio_store.load_audio(audio_id)
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", artifact.content_type)
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                except ValueError as error:
                    self._send_error(HTTPStatus.NOT_FOUND, str(error))
                return
            if self.path != "/api/garden-preview":
                self._send_error(HTTPStatus.NOT_FOUND, "接口不存在")
                return
            try:
                payload = interaction_service.get_preview(preview_garden_id)
                self._send_json(HTTPStatus.OK, payload.model_dump(mode="json"))
            except ValueError as error:
                self._send_error(HTTPStatus.NOT_FOUND, str(error))
            except Exception as error:
                self._send_error(HTTPStatus.SERVICE_UNAVAILABLE, str(error))

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/api/creations" and creation_service is not None:
                try:
                    request = CreateMemoryRequest.model_validate_json(self._read_body())
                    result = creation_service.create_memory(
                        request.text,
                        request.garden_id,
                        (request.x, request.y),
                    )
                    self._send_json(HTTPStatus.CREATED, result)
                except (ValidationError, ValueError) as error:
                    self._send_error(HTTPStatus.BAD_REQUEST, str(error))
                except Exception as error:
                    self._send_error(HTTPStatus.SERVICE_UNAVAILABLE, str(error))
                return
            music_match = _MUSIC_PATH.fullmatch(self.path)
            if music_match is not None and creation_service is not None:
                try:
                    request = RegenerateMusicRequest.model_validate_json(self._read_body())
                    result = creation_service.regenerate_music(
                        UUID(music_match.group("creation_id")),
                        request.modification_text,
                    )
                    self._send_json(HTTPStatus.CREATED, result)
                except (ValidationError, ValueError) as error:
                    self._send_error(HTTPStatus.BAD_REQUEST, str(error))
                except Exception as error:
                    self._send_error(HTTPStatus.SERVICE_UNAVAILABLE, str(error))
                return
            selection_match = _MUSIC_SELECTION_PATH.fullmatch(self.path)
            if selection_match is not None and creation_service is not None:
                try:
                    request = SelectMusicVersionRequest.model_validate_json(self._read_body())
                    result = creation_service.select_music_version(
                        UUID(selection_match.group("creation_id")),
                        request.audio_artifact_id,
                    )
                    self._send_json(HTTPStatus.OK, result)
                except (ValidationError, ValueError) as error:
                    self._send_error(HTTPStatus.BAD_REQUEST, str(error))
                except Exception as error:
                    self._send_error(HTTPStatus.SERVICE_UNAVAILABLE, str(error))
                return
            self._send_error(HTTPStatus.NOT_FOUND, "接口不存在")

        def do_DELETE(self) -> None:  # noqa: N802
            match = _DIG_PATH.fullmatch(self.path)
            if match is None or creation_service is None:
                self._send_error(HTTPStatus.NOT_FOUND, "接口不存在")
                return
            try:
                garden_id = UUID(match.group("garden_id"))
                planting_id = UUID(match.group("planting_id"))
                creation_service.dig_up_flower(garden_id, planting_id)
                payload = interaction_service.get_preview(garden_id)
                self._send_json(HTTPStatus.OK, payload.model_dump(mode="json"))
            except ValueError as error:
                self._send_error(HTTPStatus.NOT_FOUND, str(error))
            except Exception as error:
                self._send_error(HTTPStatus.SERVICE_UNAVAILABLE, str(error))

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16_384:
                raise ValueError("请求体长度无效")
            return self.rfile.read(length)

        def _send_json(self, status: HTTPStatus, payload: object) -> None:
            body = json.dumps(_json_safe_payload(payload), ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error(self, status: HTTPStatus, message: str) -> None:
            self._send_json(status, {"error": message})

    return GardenPreviewHandler


def run_server(
    interaction_service: GardenInteractionService,
    preview_garden_id: UUID,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    creation_service: CreationService | None = None,
) -> None:
    handler = create_handler(interaction_service, preview_garden_id, creation_service)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Garden preview API: http://{host}:{port}")
    server.serve_forever()

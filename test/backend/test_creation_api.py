"""正式创作 HTTP 契约；生成服务用替身以避免调用外部模型。"""

import json
from http import HTTPStatus
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from backend.app.api.garden_preview import create_handler


def post(handler_type, path, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler = handler_type.__new__(handler_type)
    handler.path = path
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = BytesIO(body)
    handler.wfile = BytesIO()
    statuses = []
    handler.send_response = statuses.append
    handler.send_header = lambda *_args: None
    handler.end_headers = lambda: None
    handler.do_POST()
    return statuses[0], json.loads(handler.wfile.getvalue())


def test_formal_creation_route_uses_schema_and_returns_creation_result():
    garden_id = uuid4()
    creation = SimpleNamespace(create_memory=Mock(return_value={
        "creation_id": str(uuid4()),
        "text": "今天完成比赛",
        "flower": {"artifact_id": str(uuid4()), "species": "tulip"},
        "planting": {"record_id": str(uuid4()), "x": 8, "y": 3},
        "music": {"artifact_id": str(uuid4()), "url": "/api/audio/test"},
    }))
    handler_type = create_handler(None, garden_id, creation)
    status, result = post(handler_type, "/api/creations", {
        "garden_id": str(garden_id), "text": "今天完成比赛", "x": 8, "y": 3,
    })
    assert status == HTTPStatus.CREATED
    creation.create_memory.assert_called_once_with("今天完成比赛", garden_id, (8, 3))
    assert result["planting"]["x"] == 8
    assert result["music"]["url"].startswith("/api/audio/")


def test_temporary_draft_route_is_removed():
    handler_type = create_handler(None, uuid4(), SimpleNamespace(create_memory=Mock()))
    status, result = post(handler_type, "/api/creations/draft", {
        "plantSpotId": "spot:8,3", "text": "今天完成比赛",
    })
    assert status == HTTPStatus.NOT_FOUND
    assert "error" in result


def test_music_selection_route_uses_stable_creation_and_audio_ids():
    creation_id = uuid4()
    audio_id = uuid4()
    creation = SimpleNamespace(select_music_version=Mock(return_value={
        "creation_id": str(creation_id),
        "music": {"artifact_id": str(audio_id), "version": 1, "url": f"/api/audio/{audio_id}"},
    }))
    handler_type = create_handler(None, uuid4(), creation)

    status, result = post(handler_type, f"/api/creations/{creation_id}/music-selection", {
        "audio_artifact_id": str(audio_id),
    })

    assert status == HTTPStatus.OK
    creation.select_music_version.assert_called_once_with(creation_id, audio_id)
    assert result["music"]["artifact_id"] == str(audio_id)

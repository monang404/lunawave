import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import json

from server.handlers.ws.discover_handlers import _handle_toggle_favorite
from core.state import AppState
from core.value_objects import VideoId

@pytest.mark.asyncio
async def test_toggle_favorite_broadcasts_favorite_status():
    ws_mock = AsyncMock()
    manager_mock = MagicMock()
    manager_mock.broadcast = AsyncMock()
    db_mock = AsyncMock()
    db_mock.toggle_favorite.return_value = True

    state = AppState()
    # Mock current_track so it matches
    track_mock = MagicMock()
    track_mock.video_id = VideoId("test_video1")
    state.current_track = track_mock
    
    app_mock = {"state": state, "db": db_mock, "manager": manager_mock}
    ws_mock.app = app_mock

    data = {
        "action": "toggle_favorite",
        "video_id": "test_video1"
    }

    await _handle_toggle_favorite(data, ws_mock, state, None, manager_mock, db_mock, None)

    # Check that broadcast was called with partial payload
    manager_mock.broadcast.assert_called_once()
    broadcast_arg = manager_mock.broadcast.call_args[0][0]
    
    assert broadcast_arg["type"] == "favorite_status"
    assert broadcast_arg["data"]["video_id"] == "test_video1"
    assert broadcast_arg["data"]["is_favorite"] is True

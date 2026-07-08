import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from server.app import create_app
from core.state import AppState, TrackInfo

import json

from server.handlers.websocket import ConnectionManager
from engine.playback.controller import PlaybackController

@pytest.fixture
def mock_playback_controller():
    controller = MagicMock(spec=PlaybackController)
    controller.state = AppState()
    return controller

@pytest.fixture
def mock_ytdlp():
    return MagicMock()

@pytest.fixture
def mock_db():
    db = MagicMock()
    async def _verify_session(*args, **kwargs):
        return True # Mock valid session
    db.verify_session = _verify_session
    return db

@pytest.mark.asyncio
async def test_critical_path_ws_play_track_to_command_bus(aiohttp_client, mock_playback_controller, mock_ytdlp, mock_db):
    """
    Simulates the critical path:
    1. Client sends a PLAY_TRACK command via WebSocket.
    2. Server receives it and executes PlayTrackCommand via CommandBus.
    """
    from core.commands import PlayTrackCommand
    app = create_app(mock_playback_controller, mock_ytdlp, mock_db, ConnectionManager())
    
    # Mock command bus
    mock_command_bus = AsyncMock()
    app["command_bus"] = mock_command_bus
    # Mock event bus as well to prevent errors
    app["event_bus"] = AsyncMock()
    
    client = await aiohttp_client(app)
    
    # Connect to WebSocket
    ws = await client.ws_connect('/ws?room=default')
    
    # Receive initial state message
    state_msg = await ws.receive_json()
    assert state_msg.get("type") == "state"
    
    # Send AUTH
    await ws.send_json({"type": "cmd", "action": "auth", "data": {"token": "valid_token"}})
    
    # Receive auth response
    auth_resp = await ws.receive_json()
    assert auth_resp.get("type") == "auth_status"
    assert auth_resp["data"]["success"] is True
    
    # Send PLAY_TRACK command
    track_data = {
        "video_id": "testvideo11",
        "title": "Test Title",
        "artist": "Test Artist"
    }
    await ws.send_json({"type": "cmd", "action": "play_track", "data": track_data})
    
    import asyncio
    await asyncio.sleep(0.2)
    
    # Verify command was executed
    executed_commands = [call[0][0] for call in mock_command_bus.execute.call_args_list if isinstance(call[0][0], PlayTrackCommand)]
    
    assert len(executed_commands) == 1
    play_cmd = executed_commands[0]
    assert play_cmd.track.video_id == "testvideo11"
    
    await ws.close()

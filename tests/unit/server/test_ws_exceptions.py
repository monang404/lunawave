import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.handlers.websocket import ws_handler


class FakeWS:
    def __init__(self, exc):
        self.exc = exc
        self.prepare = AsyncMock()
        self.send_str = AsyncMock()

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise self.exc

@pytest.mark.asyncio
async def test_ws_handler_catches_cancelled_error():
    request = MagicMock()
    request.app = {"manager": MagicMock(), "state": MagicMock(), "db": MagicMock(), "ytdlp": MagicMock(), "command_bus": MagicMock(), "playback_controller": MagicMock()}
    request.app["manager"].connect = AsyncMock()
    request.app["state"].to_dict.return_value = {}

    ws = FakeWS(asyncio.CancelledError())

    with patch("server.handlers.websocket.web.WebSocketResponse", return_value=ws):
        with patch("server.handlers.websocket.logger.debug") as debug_mock:
            await ws_handler(request)
            debug_mock.assert_called_with("WebSocket connection cancelled")

@pytest.mark.asyncio
async def test_ws_handler_catches_connection_error():
    request = MagicMock()
    request.app = {"manager": MagicMock(), "state": MagicMock(), "db": MagicMock(), "ytdlp": MagicMock(), "command_bus": MagicMock(), "playback_controller": MagicMock()}
    request.app["manager"].connect = AsyncMock()
    request.app["state"].to_dict.return_value = {}

    ws = FakeWS(ConnectionError("Test connection error"))

    with patch("server.handlers.websocket.web.WebSocketResponse", return_value=ws):
        with patch("server.handlers.websocket.logger.info") as info_mock:
            await ws_handler(request)
            info_mock.assert_called_with("WebSocket client disconnected: Test connection error")

@pytest.mark.asyncio
async def test_ws_handler_catches_generic_error():
    request = MagicMock()
    request.app = {"manager": MagicMock(), "state": MagicMock(), "db": MagicMock(), "ytdlp": MagicMock(), "command_bus": MagicMock(), "playback_controller": MagicMock()}
    request.app["manager"].connect = AsyncMock()
    request.app["state"].to_dict.return_value = {}

    ws = FakeWS(ValueError("Some value error"))

    with patch("server.handlers.websocket.web.WebSocketResponse", return_value=ws):
        with patch("server.handlers.websocket.logger.error") as error_mock:
            await ws_handler(request)
            error_mock.assert_called_with("WebSocket error: Some value error")

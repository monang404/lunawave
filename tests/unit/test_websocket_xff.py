import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from aiohttp import WSMsgType
from server.handlers.websocket import ws_handler

@pytest.mark.asyncio
async def test_websocket_xff_anti_spoofing():
    # Arrange
    request = MagicMock()
    request.remote = "127.0.0.1"

    # Simulate attacker sending "8.8.8.8", and trusted proxy appending "192.168.1.5"
    request.headers = {"X-Forwarded-For": "8.8.8.8, 192.168.1.5"}

    app = {
        "playback_controller": MagicMock(),
        "state": MagicMock(),
        "manager": MagicMock(),
        "db": MagicMock(),
        "ytdlp": MagicMock(),
        "command_bus": MagicMock()
    }
    app["state"].to_dict.return_value = {}
    app["manager"].connect = AsyncMock()
    app["manager"].disconnect = MagicMock()
    request.app = app

    msg = MagicMock()
    msg.type = WSMsgType.TEXT
    msg.data = json.dumps({"type": "cmd", "action": "some_action"})

    # Simulate async generator for ws
    async def async_gen():
        yield msg
        msg2 = MagicMock()
        msg2.type = WSMsgType.CLOSE
        yield msg2

    ws_mock = MagicMock()
    ws_mock.prepare = AsyncMock()
    ws_mock.send_str = AsyncMock()
    ws_mock.__aiter__ = lambda self: async_gen()

    with patch("server.handlers.websocket.web.WebSocketResponse", return_value=ws_mock):
        with patch("server.handlers.websocket.handle_ws_message", new_callable=AsyncMock) as mock_handle:
            with patch("server.handlers.websocket.TRUSTED_PROXY", True):
                # Act
                await ws_handler(request)

                # Assert
                mock_handle.assert_called_once()
                args, kwargs = mock_handle.call_args

                # The client_ip is the 3rd positional argument
                extracted_ip = args[2]

                # It should take the last IP, not the spoofed first IP
                assert extracted_ip == "192.168.1.5"
                assert extracted_ip != "8.8.8.8"

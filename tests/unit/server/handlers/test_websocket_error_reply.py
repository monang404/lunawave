import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.handlers.websocket import handle_ws_message


@pytest.mark.asyncio
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
async def test_websocket_error_reply_generic(mock_check_rate_limit, capsys):
    mock_ws = AsyncMock()
    mock_manager = MagicMock()
    mock_repos = MagicMock()
    mock_command_bus = AsyncMock()

    with patch("server.handlers.websocket.require_auth", return_value=True):
        with patch(
            "server.handlers.websocket.handle_playback_command",
            side_effect=ValueError("Secret Error"),
        ):
            await handle_ws_message(
                {"type": "cmd", "action": "play_track", "data": {}},
                mock_ws,
                "127.0.0.1",
                None,
                None,
                mock_manager,
                mock_repos,
                mock_command_bus,
            )

    assert mock_ws.send_str.called
    sent_data = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_data["type"] == "error"
    assert sent_data["data"] == "Terjadi kesalahan saat memproses permintaan."
    assert "Secret Error" not in sent_data["data"]

    captured = capsys.readouterr()
    assert "Secret Error" in captured.out or "Secret Error" in captured.err


@pytest.mark.asyncio
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
async def test_websocket_error_reply_debug_mode(mock_check_rate_limit, monkeypatch):
    import config

    monkeypatch.setattr(config, "DEBUG_EXPOSE_ERRORS", True)

    mock_ws = AsyncMock()
    mock_manager = MagicMock()
    mock_repos = MagicMock()
    mock_command_bus = AsyncMock()

    with patch("server.handlers.websocket.require_auth", return_value=True):
        with patch(
            "server.handlers.websocket.handle_playback_command",
            side_effect=ValueError("Secret Error"),
        ):
            await handle_ws_message(
                {"type": "cmd", "action": "play_track", "data": {}},
                mock_ws,
                "127.0.0.1",
                None,
                None,
                mock_manager,
                mock_repos,
                mock_command_bus,
            )

    assert mock_ws.send_str.called
    sent_data = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_data["type"] == "error"
    assert sent_data["data"] == "Secret Error"

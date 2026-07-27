import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.handlers.websocket import handle_ws_message


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
async def test_handle_ws_message_logout_all(mock_require_auth):
    mock_ws = AsyncMock()
    mock_ws2 = AsyncMock()
    mock_manager = MagicMock()
    mock_manager.authenticated_connections = {mock_ws, mock_ws2}
    mock_repos = MagicMock()
    mock_repos.sessions = AsyncMock()

    await handle_ws_message(
        {"type": "cmd", "action": "logout_all", "data": {}},
        mock_ws,
        "127.0.0.1",
        None,
        None,
        mock_manager,
        mock_repos,
        command_bus=AsyncMock(),
    )

    mock_repos.sessions.delete_all_sessions.assert_called_once()
    assert len(mock_manager.authenticated_connections) == 0


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=False)
async def test_handle_ws_message_logout_all_non_admin(mock_require_auth):
    mock_ws = AsyncMock()
    mock_manager = MagicMock()
    mock_manager.authenticated_connections = {AsyncMock()}
    mock_repos = MagicMock()
    mock_repos.sessions = AsyncMock()

    await handle_ws_message(
        {"type": "cmd", "action": "logout_all", "data": {}},
        mock_ws,
        "127.0.0.1",
        None,
        None,
        mock_manager,
        mock_repos,
        command_bus=AsyncMock(),
    )

    mock_repos.sessions.delete_all_sessions.assert_not_called()
    assert len(mock_manager.authenticated_connections) == 1
    assert mock_ws.send_str.called
    sent_data = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_data["type"] == "error"
    assert "Akses ditolak" in sent_data["data"]

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.handlers.websocket import handle_ws_message


@pytest.mark.asyncio
@patch("server.handlers.websocket.handle_auth")
async def test_handle_ws_message_auth(mock_handle_auth):
    mock_ws = AsyncMock()
    mock_manager = MagicMock()
    mock_db = MagicMock()

    await handle_ws_message(
        {"type": "cmd", "action": "auth", "data": {"token": "123"}},
        mock_ws,
        "127.0.0.1",
        None,
        None,
        mock_manager,
        mock_db,
    )

    mock_handle_auth.assert_called_once()
    args, kwargs = mock_handle_auth.call_args
    assert args[0] == mock_ws
    assert args[1] == {"token": "123"}
    assert args[2] == mock_manager
    assert args[3] == "127.0.0.1"
    assert args[4] == mock_db.sessions


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=False)
async def test_handle_ws_message_unauthenticated(mock_require_auth):
    mock_ws = AsyncMock()
    await handle_ws_message(
        {"type": "cmd", "action": "play_track"}, mock_ws, "127.0.0.1", None, None, None, None
    )
    mock_ws.send_str.assert_called_once()
    assert "Akses ditolak" in mock_ws.send_str.call_args[0][0]


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=False)
async def test_handle_ws_message_rate_limited(mock_check_rate, mock_require_auth):
    mock_ws = AsyncMock()
    await handle_ws_message(
        {"type": "cmd", "action": "play_track"}, mock_ws, "127.0.0.1", None, None, None, None
    )
    mock_ws.send_str.assert_called_once()
    assert "Terlalu banyak permintaan" in mock_ws.send_str.call_args[0][0]


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
@patch("server.handlers.websocket.handle_playback_command")
async def test_handle_ws_message_playback_routing(mock_handle_playback, mock_check, mock_require):
    await handle_ws_message(
        {"type": "cmd", "action": "play_track", "data": {}},
        AsyncMock(),
        "127.0.0.1",
        None,
        None,
        None,
        None,
    )
    mock_handle_playback.assert_called_once_with("play_track", {})


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
@patch("server.handlers.websocket.handle_queue_command")
async def test_handle_ws_message_queue_routing(mock_handle_queue, mock_check, mock_require):
    mock_db = MagicMock()
    await handle_ws_message(
        {"type": "cmd", "action": "queue_add", "data": {}},
        AsyncMock(),
        "127.0.0.1",
        None,
        None,
        None,
        mock_db,
    )
    mock_handle_queue.assert_called_once_with("queue_add", {}, mock_db.artists, mock_db.genres)


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
@patch("server.handlers.websocket.handle_playback_command")
async def test_handle_ws_message_disconnect_during_send(
    mock_handle_playback, mock_check, mock_require
):
    mock_ws = AsyncMock()
    mock_handle_playback.side_effect = Exception("Simulated handler error")
    mock_ws.send_str.side_effect = ConnectionResetError("Disconnected during send")

    await handle_ws_message(
        {"type": "cmd", "action": "play_track", "data": {}},
        mock_ws,
        "127.0.0.1",
        None,
        None,
        None,
        None,
    )
    mock_ws.send_str.assert_called_once()


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
@patch("server.handlers.websocket.handle_playback_command")
async def test_handle_ws_message_malformed_payload(mock_handle_playback, mock_check, mock_require):
    mock_ws = AsyncMock()

    # Missing 'data' field
    await handle_ws_message(
        {"type": "cmd", "action": "play_track"},
        mock_ws,
        "127.0.0.1",
        None,
        None,
        None,
        None,
    )

    mock_handle_playback.assert_called_once_with("play_track", {})


@pytest.mark.parametrize(
    "action",
    [
        "stop",
        "set_sleep_timer",
        "set_speed",
        "set_loop",
        "set_crossfade",
        "set_loudness_normalization",
    ],
)
@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
@patch("server.handlers.websocket.handle_playback_command")
async def test_new_playback_actions_are_routed(
    mock_handle_playback, mock_check, mock_require, action
):
    """Verifikasi action baru (PATCH-058, PATCH-061) di-route ke handle_playback_command."""
    await handle_ws_message(
        {"type": "cmd", "action": action, "data": {}},
        AsyncMock(),
        "127.0.0.1",
        None,
        None,
        None,
        None,
    )
    mock_handle_playback.assert_called_once_with(action, {})


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
async def test_cache_commands_are_routed(mock_check, mock_require):
    """Verifikasi get_cache_size dan clear_cache di-route ke ws_cache handler."""
    with patch("server.handlers.ws_cache.handle_cache_command") as mock_cache:
        mock_ws = AsyncMock()
        await handle_ws_message(
            {"type": "cmd", "action": "get_cache_size", "data": {}},
            mock_ws,
            "127.0.0.1",
            None,
            None,
            MagicMock(),
            MagicMock(),
        )
        mock_cache.assert_called_once()


@pytest.mark.asyncio
@patch("server.handlers.websocket.require_auth", return_value=True)
@patch("server.handlers.websocket.check_rate_limit", return_value=True)
async def test_unknown_action_does_not_crash(mock_check, mock_require):
    """Action tidak dikenal harus diabaikan tanpa error/exception."""
    mock_ws = AsyncMock()
    await handle_ws_message(
        {"type": "cmd", "action": "action_yang_tidak_ada", "data": {}},
        mock_ws,
        "127.0.0.1",
        None,
        None,
        None,
        None,
    )
    # Tidak boleh crash, tidak boleh kirim error ke client
    mock_ws.send_str.assert_not_called()

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.handlers.websocket import handle_ws_message


@pytest.mark.asyncio
async def test_handle_ws_message_data_not_dict():
    # If data is a string, it should not crash, it should convert data to {}
    msg = {
        "type": "cmd",
        "action": "auth",
        "data": "this is a string, not a dict"
    }

    ws = MagicMock()
    manager = MagicMock()
    # Mock require_auth to not be needed since auth action will handle it, or we just patch handle_auth

    with patch("server.handlers.websocket.handle_auth", new_callable=AsyncMock) as mock_handle_auth:
        await handle_ws_message(
            msg=msg,
            ws=ws,
            client_ip="127.0.0.1",
            state=MagicMock(),
            ytdlp=MagicMock(),
            manager=manager,
            db=MagicMock(),
            command_bus=MagicMock()
        )

        # It should pass {} as data to handle_auth instead of the string
        mock_handle_auth.assert_called_once()
        called_data = mock_handle_auth.call_args[0][1]
        assert called_data == {}

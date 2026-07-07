import pytest
from unittest.mock import MagicMock, AsyncMock
from server.handlers.auth import handle_auth, handle_logout
import json

@pytest.mark.asyncio
async def test_auth_token_rotation():
    # Arrange
    manager = MagicMock()
    manager.rl_lock = AsyncMock()
    manager.rl_lock.__aenter__ = AsyncMock()
    manager.rl_lock.__aexit__ = AsyncMock()
    manager.login_attempts = {}
    manager.command_history = {}
    manager.authenticated_connections = set()

    ws = AsyncMock()
    db = AsyncMock()

    data = {"username": "admin", "password": "password"} # we'll mock verify_password and get_admin_password

    with pytest.MonkeyPatch.context() as m:
        m.setattr("server.handlers.auth.ADMIN_USERNAME", "admin")
        m.setattr("server.handlers.auth.get_admin_password", lambda: "hash")
        m.setattr("server.handlers.auth.verify_password", lambda p, h: True)

        # Act
        await handle_auth(ws, data, manager, "127.0.0.1", db, 1000.0)

        # Assert
        ws.send_str.assert_called_once()
        resp = json.loads(ws.send_str.call_args[0][0])
        assert resp["type"] == "auth_status"
        assert resp["data"]["success"] is True

        token = resp["data"]["token"]
        assert len(token) == 64 # 32 bytes hex = 64 chars

        db.create_session.assert_called_once()
        assert ws in manager.authenticated_connections

        # Now test logout
        ws.send_str.reset_mock()
        await handle_logout(ws, {"token": token}, manager, db)

        db.delete_session.assert_called_once_with(token)
        assert ws not in manager.authenticated_connections
        ws.send_str.assert_called_once()
        resp = json.loads(ws.send_str.call_args[0][0])
        assert resp["data"]["success"] is False
        assert "Logged out" in resp["data"]["message"]

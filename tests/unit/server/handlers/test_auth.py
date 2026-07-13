"""
Module: tests.unit.server.handlers.test_auth

Purpose:
    Unit tests for server.handlers.auth — session token verification,
    credential validation, rate limiting, and stale IP pruning.
    All I/O (DB, WebSocket) is mocked.

Subscribes to:
    None

Publishes:
    None
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manager():
    mgr = MagicMock()
    mgr.rl_lock = MagicMock()
    mgr.rl_lock.__aenter__ = AsyncMock(return_value=None)
    mgr.rl_lock.__aexit__ = AsyncMock(return_value=None)
    mgr.authenticated_connections = set()
    mgr.login_attempts = {}
    mgr.command_history = {}
    return mgr


def make_ws():
    ws = MagicMock()
    ws.send_str = AsyncMock()
    return ws


def make_db(session_valid: bool = False):
    db = MagicMock()
    db.verify_session = AsyncMock(return_value=session_valid)
    db.create_session = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# _prune_stale_ips
# ---------------------------------------------------------------------------

class TestPruneStaleIps:
    def test_removes_stale_auth_ips(self):
        from server.handlers.auth import _prune_stale_ips
        mgr = make_manager()
        old_time = 0  # effectively expired
        mgr.login_attempts = {"192.168.1.1": [old_time]}
        mgr.command_history = {}

        _prune_stale_ips(mgr, now=9999)

        assert "192.168.1.1" not in mgr.login_attempts

    def test_keeps_recent_auth_ips(self):
        from server.handlers.auth import _prune_stale_ips
        mgr = make_manager()
        mgr.login_attempts = {"192.168.1.2": [9990]}  # within 5 min
        mgr.command_history = {}

        _prune_stale_ips(mgr, now=9999)

        assert "192.168.1.2" in mgr.login_attempts

    def test_removes_stale_command_ips(self):
        from server.handlers.auth import _prune_stale_ips
        mgr = make_manager()
        mgr.login_attempts = {}
        mgr.command_history = {"10.0.0.1": [0]}  # expired (>60s)

        _prune_stale_ips(mgr, now=9999)

        assert "10.0.0.1" not in mgr.command_history


# ---------------------------------------------------------------------------
# handle_auth — session token path
# ---------------------------------------------------------------------------

class TestHandleAuthToken:
    @pytest.mark.asyncio
    async def test_valid_token_authenticates_connection(self):
        from server.handlers.auth import handle_auth
        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=True)

        await handle_auth(ws, {"token": "valid_token"}, mgr, "127.0.0.1", db, now=1000)

        assert ws in mgr.authenticated_connections
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is True
        assert sent["data"]["token"] == "valid_token"

    @pytest.mark.asyncio
    async def test_invalid_token_falls_through_to_credential_check(self):
        from server.handlers.auth import handle_auth
        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False)

        with patch("server.handlers.auth.ADMIN_USERNAME", "admin"), \
             patch("server.handlers.auth.ADMIN_PASSWORD", "hashed"), \
             patch("server.handlers.auth.verify_password", return_value=False), \
             patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=False)
            await handle_auth(
                ws, {"token": "bad_token", "username": "admin", "password": "wrong"},
                mgr, "127.0.0.1", db, now=1000
            )

        assert ws not in mgr.authenticated_connections
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False


# ---------------------------------------------------------------------------
# handle_auth — credential path
# ---------------------------------------------------------------------------

class TestHandleAuthCredentials:
    @pytest.mark.asyncio
    async def test_correct_credentials_authenticate_and_create_session(self):
        from server.handlers.auth import handle_auth
        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False)

        with patch("server.handlers.auth.ADMIN_USERNAME", "admin"), \
             patch("server.handlers.auth.ADMIN_PASSWORD", "hashed"), \
             patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
            await handle_auth(
                ws, {"username": "admin", "password": "correct"},
                mgr, "127.0.0.1", db, now=1000
            )

        assert ws in mgr.authenticated_connections
        db.create_session.assert_awaited_once()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is True
        assert "token" in sent["data"]

    @pytest.mark.asyncio
    async def test_wrong_credentials_send_failure_and_record_attempt(self):
        from server.handlers.auth import handle_auth
        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False)

        with patch("server.handlers.auth.ADMIN_USERNAME", "admin"), \
             patch("server.handlers.auth.ADMIN_PASSWORD", "hashed"), \
             patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=False)
            await handle_auth(
                ws, {"username": "admin", "password": "wrong"},
                mgr, "127.0.0.1", db, now=1000
            )

        assert ws not in mgr.authenticated_connections
        assert len(mgr.login_attempts.get("127.0.0.1", [])) == 1
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_after_5_failures(self):
        from server.handlers.auth import handle_auth
        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False)
        # Simulate 5 recent failed attempts
        mgr.login_attempts["10.0.0.5"] = [995, 996, 997, 998, 999]

        with patch("server.handlers.auth.ADMIN_USERNAME", "admin"), \
             patch("server.handlers.auth.ADMIN_PASSWORD", "hashed"), \
             patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=False)
            await handle_auth(
                ws, {"username": "admin", "password": "wrong"},
                mgr, "10.0.0.5", db, now=1000
            )

        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "Terlalu banyak" in sent["data"]["message"]

    @pytest.mark.asyncio
    async def test_successful_login_clears_attempt_record(self):
        from server.handlers.auth import handle_auth
        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False)
        mgr.login_attempts["10.0.0.6"] = [998]

        with patch("server.handlers.auth.ADMIN_USERNAME", "admin"), \
             patch("server.handlers.auth.ADMIN_PASSWORD", "hashed"), \
             patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
            await handle_auth(
                ws, {"username": "admin", "password": "correct"},
                mgr, "10.0.0.6", db, now=1000
            )

        assert "10.0.0.6" not in mgr.login_attempts


# ---------------------------------------------------------------------------
# require_auth
# ---------------------------------------------------------------------------

class TestRequireAuth:
    def test_returns_true_when_ws_in_authenticated(self):
        from server.handlers.auth import require_auth
        mgr = make_manager()
        ws = make_ws()
        mgr.authenticated_connections.add(ws)
        assert require_auth(mgr, ws) is True

    def test_returns_false_when_ws_not_authenticated(self):
        from server.handlers.auth import require_auth
        mgr = make_manager()
        ws = make_ws()
        assert require_auth(mgr, ws) is False

"""
Module: tests.unit.server.handlers.test_setup

Purpose:
    Unit tests for server.handlers.setup -- input validation, hashing +
    persist, submit-ganda / race condition handling, rate limiting, and
    the GET /api/setup-required endpoint. All I/O (DB, WebSocket) is mocked.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - server.handlers.setup

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import json
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.app import REPOS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_manager():
    mgr = MagicMock()
    mgr.rl_lock = MagicMock()
    mgr.rl_lock.__aenter__ = AsyncMock(return_value=None)
    mgr.rl_lock.__aexit__ = AsyncMock(return_value=None)
    mgr.setup_attempts = {}
    return mgr


def make_ws():
    ws = MagicMock()
    ws.send_str = AsyncMock()
    return ws


def make_repos(exists: bool = False):
    repos = MagicMock()
    repos.admin_account = MagicMock()
    repos.admin_account.admin_account_exists = AsyncMock(return_value=exists)
    repos.admin_account.create_admin_account = AsyncMock()
    return repos


# ---------------------------------------------------------------------------
# handle_setup_admin -- validasi input
# ---------------------------------------------------------------------------


class TestHandleSetupAdminValidation:
    @pytest.mark.asyncio
    async def test_empty_username_rejected(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos()

        await handle_setup_admin(
            ws, {"username": "", "password": "longenough"}, mgr, "127.0.0.1", repos, now=1000
        )

        repos.admin_account.create_admin_account.assert_not_awaited()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "Username" in sent["data"]["message"]

    @pytest.mark.asyncio
    async def test_password_too_short_rejected(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos()

        await handle_setup_admin(
            ws, {"username": "admin", "password": "short"}, mgr, "127.0.0.1", repos, now=1000
        )

        repos.admin_account.create_admin_account.assert_not_awaited()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "Password" in sent["data"]["message"]


# ---------------------------------------------------------------------------
# handle_setup_admin -- sukses (hashing & simpan akun)
# ---------------------------------------------------------------------------


class TestHandleSetupAdminSuccess:
    @pytest.mark.asyncio
    async def test_valid_input_hashes_and_saves_account(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos(exists=False)

        with patch(
            "server.handlers.setup.hash_password", return_value="pbkdf2:sha256:hashed"
        ) as hp:
            await handle_setup_admin(
                ws,
                {"username": "admin", "password": "longenough123"},
                mgr,
                "127.0.0.1",
                repos,
                now=1000,
            )

        hp.assert_called_once_with("longenough123")
        repos.admin_account.create_admin_account.assert_awaited_once_with(
            "admin", "pbkdf2:sha256:hashed"
        )
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_username_whitespace_is_stripped(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos(exists=False)

        await handle_setup_admin(
            ws,
            {"username": "  admin  ", "password": "longenough123"},
            mgr,
            "127.0.0.1",
            repos,
            now=1000,
        )

        repos.admin_account.create_admin_account.assert_awaited_once()
        called_username = repos.admin_account.create_admin_account.call_args[0][0]
        assert called_username == "admin"


# ---------------------------------------------------------------------------
# handle_setup_admin -- race condition submit ganda
# ---------------------------------------------------------------------------


class TestHandleSetupAdminDoubleSubmit:
    @pytest.mark.asyncio
    async def test_second_submit_after_account_exists_rejected(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos(exists=True)

        await handle_setup_admin(
            ws,
            {"username": "admin", "password": "longenough123"},
            mgr,
            "127.0.0.1",
            repos,
            now=1000,
        )

        repos.admin_account.create_admin_account.assert_not_awaited()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "sudah pernah dibuat" in sent["data"]["message"]

    @pytest.mark.asyncio
    async def test_concurrent_submit_hits_unique_constraint_not_overwrite(self):
        """Dua request nyaris bersamaan lolos cek exists() (keduanya lihat
        False), tapi create_admin_account() melempar IntegrityError untuk
        request kedua -- tidak boleh overwrite diam-diam."""
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos(exists=False)
        repos.admin_account.create_admin_account = AsyncMock(
            side_effect=sqlite3.IntegrityError("UNIQUE constraint failed: admin_account.username")
        )

        await handle_setup_admin(
            ws,
            {"username": "admin", "password": "longenough123"},
            mgr,
            "127.0.0.1",
            repos,
            now=1000,
        )

        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "sudah pernah dibuat" in sent["data"]["message"]


# ---------------------------------------------------------------------------
# handle_setup_admin -- rate limit
# ---------------------------------------------------------------------------


class TestHandleSetupAdminRateLimit:
    @pytest.mark.asyncio
    async def test_sixth_attempt_within_5_minutes_rejected(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        mgr.setup_attempts["10.0.0.9"] = [995, 996, 997, 998, 999]
        repos = make_repos(exists=False)

        await handle_setup_admin(
            ws, {"username": "admin", "password": "wrongshort"}, mgr, "10.0.0.9", repos, now=1000
        )

        repos.admin_account.create_admin_account.assert_not_awaited()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "Terlalu banyak" in sent["data"]["message"]

    @pytest.mark.asyncio
    async def test_stale_attempts_pruned_before_counting(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        # 5 percobaan tapi semuanya sudah di luar window 300s -> harus diprune.
        mgr.setup_attempts["10.0.0.10"] = [0, 1, 2, 3, 4]
        repos = make_repos(exists=False)

        await handle_setup_admin(
            ws,
            {"username": "admin", "password": "longenough123"},
            mgr,
            "10.0.0.10",
            repos,
            now=1000,
        )

        repos.admin_account.create_admin_account.assert_awaited_once()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_input_counts_toward_rate_limit(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos(exists=False)

        await handle_setup_admin(
            ws, {"username": "", "password": ""}, mgr, "10.0.0.11", repos, now=1000
        )

        assert len(mgr.setup_attempts.get("10.0.0.11", [])) == 1


# ---------------------------------------------------------------------------
# handle_setup_admin -- fallback kegagalan (T-B7)
# ---------------------------------------------------------------------------


class TestHandleSetupAdminFailureFallback:
    @pytest.mark.asyncio
    async def test_db_failure_on_create_returns_clear_error_without_crashing(self):
        """DB corrupt / disk penuh saat INSERT -- handler tidak boleh
        melempar exception ke luar (server tetap hidup), client dapat
        pesan jelas tanpa detail internal bocor."""
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos(exists=False)
        repos.admin_account.create_admin_account = AsyncMock(side_effect=OSError("disk I/O error"))

        # Tidak boleh raise -- ini yang membuktikan "server tetap start".
        await handle_setup_admin(
            ws,
            {"username": "admin", "password": "longenough123"},
            mgr,
            "127.0.0.1",
            repos,
            now=1000,
        )

        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        # Pesan tidak boleh membocorkan detail internal (path, exception raw).
        assert "disk I/O error" not in sent["data"]["message"]
        assert "Gagal menyimpan" in sent["data"]["message"]

    @pytest.mark.asyncio
    async def test_db_failure_on_exists_check_returns_clear_error_and_skips_insert(self):
        from server.handlers.setup import handle_setup_admin

        ws = make_ws()
        mgr = make_manager()
        repos = make_repos()
        repos.admin_account.admin_account_exists = AsyncMock(
            side_effect=sqlite3.OperationalError("database disk image is malformed")
        )

        await handle_setup_admin(
            ws,
            {"username": "admin", "password": "longenough123"},
            mgr,
            "127.0.0.1",
            repos,
            now=1000,
        )

        repos.admin_account.create_admin_account.assert_not_awaited()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "database disk image" not in sent["data"]["message"]


class TestSetupRequiredEndpointFailureFallback:
    @pytest.mark.asyncio
    async def test_db_failure_returns_503_without_crashing(self):
        from server.handlers.setup import setup_required

        repos = make_repos()
        repos.admin_account.admin_account_exists = AsyncMock(
            side_effect=sqlite3.OperationalError("database disk image is malformed")
        )
        request = MagicMock()
        request.app = {REPOS: repos}

        resp = await setup_required(request)

        assert resp.status == 503
        assert "database disk image" not in json.loads(resp.body)["error"]


class TestSetupRequiredEndpoint:
    @pytest.mark.asyncio
    async def test_returns_true_when_no_account_exists(self):
        from server.handlers.setup import setup_required

        repos = make_repos(exists=False)
        request = MagicMock()
        request.app = {REPOS: repos}

        resp = await setup_required(request)

        assert json.loads(resp.body)["setup_required"] is True

    @pytest.mark.asyncio
    async def test_returns_false_when_account_already_exists(self):
        from server.handlers.setup import setup_required

        repos = make_repos(exists=True)
        request = MagicMock()
        request.app = {REPOS: repos}

        resp = await setup_required(request)

        assert json.loads(resp.body)["setup_required"] is False

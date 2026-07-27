"""
Module: tests.unit.server.handlers.test_auth

Purpose:
    Unit tests for server.handlers.auth — session token verification,
    credential validation, rate limiting, and stale IP pruning.
    All I/O (DB, WebSocket) is mocked.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - server.handlers.auth

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_structlog():
    import structlog

    structlog.reset_defaults()


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


def make_db(session_valid: bool = False, account=None):
    """Fake `repos` (bukan cuma sessions lagi, T-B13.1): punya
    `.sessions` (session_repo-like) dan `.admin_account`
    (admin_account_repo-like). `account`, kalau diisi, dict biasa
    (mendukung akses `["username"]`/`["password_hash"]` seperti
    aiosqlite.Row) -- None berarti admin_account belum ada (instalasi
    baru, belum lewat Initial Setup).
    """
    db = MagicMock()
    db.sessions = MagicMock()
    db.sessions.verify_session = AsyncMock(return_value=session_valid)
    db.sessions.create_session = AsyncMock()
    db.sessions.extend_session = AsyncMock()
    db.admin_account = MagicMock()
    db.admin_account.get_admin_account = AsyncMock(return_value=account)
    return db


ADMIN_ACCOUNT = {"username": "admin", "password_hash": "hashed"}


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
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)

        with (
            patch("server.handlers.auth.verify_password", return_value=False),
            patch("asyncio.get_running_loop") as mock_loop,
        ):
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=False)
            await handle_auth(
                ws,
                {"token": "bad_token", "username": "admin", "password": "wrong"},
                mgr,
                "127.0.0.1",
                db,
                now=1000,
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
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
            await handle_auth(
                ws, {"username": "admin", "password": "correct"}, mgr, "127.0.0.1", db, now=1000
            )

        assert ws in mgr.authenticated_connections
        db.sessions.create_session.assert_awaited_once()
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is True
        assert "token" in sent["data"]

    @pytest.mark.asyncio
    async def test_wrong_username_still_runs_password_verification(self):
        """PATCH-2026-07-16-001 regression: verify_password (via
        run_in_executor) must always run, even when the username is wrong,
        so response timing can't be used to enumerate valid usernames."""
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)

        with patch("asyncio.get_running_loop") as mock_loop:
            executor_mock = AsyncMock(return_value=True)
            mock_loop.return_value.run_in_executor = executor_mock
            await handle_auth(
                ws,
                {"username": "not_admin", "password": "whatever"},
                mgr,
                "127.0.0.1",
                db,
                now=1000,
            )

        executor_mock.assert_awaited_once()
        assert ws not in mgr.authenticated_connections
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False

    @pytest.mark.asyncio
    async def test_no_admin_account_yet_still_runs_password_verification(self):
        """T-B13.1 regression: kalau admin_account belum ada sama sekali
        (instalasi baru, belum lewat Initial Setup), verify_password tetap
        harus dijalankan (terhadap dummy hash) -- bukan short-circuit fail
        instan -- demi mempertahankan mitigasi timing side-channel
        PATCH-2026-07-16-001 walau sumber datanya sekarang admin_account."""
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False, account=None)

        with patch("asyncio.get_running_loop") as mock_loop:
            executor_mock = AsyncMock(return_value=True)  # walau "cocok" secara hash
            mock_loop.return_value.run_in_executor = executor_mock
            await handle_auth(
                ws,
                {"username": "admin", "password": "whatever"},
                mgr,
                "127.0.0.1",
                db,
                now=1000,
            )

        executor_mock.assert_awaited_once()
        # Tidak ada admin_account -> login TIDAK BOLEH berhasil meski
        # verify_password (dummy) mengembalikan True.
        assert ws not in mgr.authenticated_connections
        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False

    @pytest.mark.asyncio
    async def test_wrong_credentials_send_failure_and_record_attempt(self):
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=False)
            await handle_auth(
                ws, {"username": "admin", "password": "wrong"}, mgr, "127.0.0.1", db, now=1000
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

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=False)
            await handle_auth(
                ws, {"username": "admin", "password": "wrong"}, mgr, "10.0.0.5", db, now=1000
            )

        sent = json.loads(ws.send_str.call_args[0][0])
        assert sent["data"]["success"] is False
        assert "Terlalu banyak" in sent["data"]["message"]

    @pytest.mark.asyncio
    async def test_successful_login_clears_attempt_record(self):
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)
        mgr.login_attempts["10.0.0.6"] = [998]

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
            await handle_auth(
                ws, {"username": "admin", "password": "correct"}, mgr, "10.0.0.6", db, now=1000
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


# ---------------------------------------------------------------------------
# Logging (task_breakdown_logging.yaml L2.1 -- G1 kritis: nol logging auth
# sebelumnya). Semua event category=LC_AUTH, component="ws.auth" (L-D1).
# Tidak pernah field password/token/stored_hash (LOGGING_STANDARD.md
# §8/§12.1) -- diverifikasi lewat capture_logs di setiap test di bawah.
# ---------------------------------------------------------------------------


class TestAuthLogging:
    _FORBIDDEN_KEYS = {"password", "token", "stored_hash"}

    @staticmethod
    def _assert_no_secret_fields(calls):
        for args, kwargs in calls:
            leaked_kwargs = TestAuthLogging._FORBIDDEN_KEYS & set(kwargs.keys())
            assert (
                not leaked_kwargs
            ), f"secret field(s) {leaked_kwargs} found in log kwargs: {kwargs}"
            if args:
                leaked_args = TestAuthLogging._FORBIDDEN_KEYS & set(args)
                assert not leaked_args, f"secret field(s) {leaked_args} found in log args: {args}"

    @pytest.mark.asyncio
    @patch("server.handlers.auth.logger")
    async def test_valid_token_logs_auth_token_verified(self, mock_logger):
        from core.log_categories import LC_AUTH
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=True)

        await handle_auth(ws, {"token": "valid_token"}, mgr, "127.0.0.1", db, now=1000)

        self._assert_no_secret_fields(mock_logger.info.call_args_list)
        mock_logger.info.assert_called_with(
            "auth_token_verified", category=LC_AUTH, client_ip="127.0.0.1"
        )

    @pytest.mark.asyncio
    @patch("server.handlers.auth.logger")
    async def test_rate_limit_logs_auth_rate_limited_warning(self, mock_logger):
        from core.log_categories import LC_AUTH
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        mgr.login_attempts = {"127.0.0.1": [999, 999, 999, 999, 999]}  # 5 recent attempts
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)

        await handle_auth(ws, {}, mgr, "127.0.0.1", db, now=1000)

        self._assert_no_secret_fields(mock_logger.warning.call_args_list)
        mock_logger.warning.assert_called_with(
            "auth_rate_limited", category=LC_AUTH, client_ip="127.0.0.1", attempt_count=5
        )

    @pytest.mark.asyncio
    @patch("server.handlers.auth.logger")
    async def test_successful_login_logs_succeeded_and_session_created(self, mock_logger):
        from core.log_categories import LC_AUTH
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
            await handle_auth(
                ws,
                {"username": "admin", "password": "correct"},
                mgr,
                "127.0.0.1",
                db,
                now=1000,
            )

        self._assert_no_secret_fields(mock_logger.info.call_args_list)
        mock_logger.info.assert_any_call(
            "auth_session_created", category=LC_AUTH, client_ip="127.0.0.1"
        )
        mock_logger.info.assert_any_call(
            "auth_login_succeeded", category=LC_AUTH, client_ip="127.0.0.1"
        )

    @pytest.mark.asyncio
    @patch("server.handlers.auth.logger")
    async def test_failed_login_logs_rejected_at_info_not_warning(self, mock_logger):
        """L-D2: satu percobaan gagal individual adalah INFO (kejadian
        normal yang diharapkan sesekali), bukan WARNING -- WARNING baru
        dipakai di auth_rate_limited saat ambang terlampaui."""
        from core.log_categories import LC_AUTH
        from server.handlers.auth import handle_auth

        ws = make_ws()
        mgr = make_manager()
        db = make_db(session_valid=False, account=ADMIN_ACCOUNT)

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=False)
            await handle_auth(
                ws, {"username": "admin", "password": "wrong"}, mgr, "127.0.0.1", db, now=1000
            )

        self._assert_no_secret_fields(mock_logger.info.call_args_list)
        mock_logger.info.assert_called_with(
            "auth_login_rejected",
            category=LC_AUTH,
            client_ip="127.0.0.1",
            reason="invalid_credentials",
        )

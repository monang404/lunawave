"""
tests/conftest.py

Shared fixtures for the LunaWave test suite.

Layout mirrors the actual package layout (core/, cache/, engine/, ...),
not the aspirational refactor target described in docs/testing.

Purpose:
    Auto-generated purpose.

Subscribes to:
    None

Publishes:
    None
"""

import os
import sys
from pathlib import Path

import pytest

_pytest_exit_status = 0

def pytest_sessionfinish(session, exitstatus):
    """Store exit status to use it if we have to force exit."""
    global _pytest_exit_status
    _pytest_exit_status = exitstatus

def pytest_unconfigure(config):
    """
    Called after all tests have finished and coverage is printed.
    If there are zombie non-daemon threads (e.g. from yt-dlp inside ThreadPoolExecutor),
    Python will hang forever on exit. This hook detects them and forces exit.
    """
    import threading
    import sys
    
    non_daemon_threads = [t for t in threading.enumerate() if not t.daemon and t.ident != threading.current_thread().ident]
    if non_daemon_threads:
        print(f"\n[WARNING] Zombie non-daemon threads detected: {non_daemon_threads}. Force exiting to prevent CI hang!", file=sys.stderr)
        os._exit(_pytest_exit_status)

# Make sure the repo root (parent of tests/) is importable as top-level
# packages: `core`, `cache`, `engine`, `config`, etc.
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# config.py auto-generates an admin password file and prints a banner the
# first time it is imported with no LUNAWAVE_ADMIN_PASS / YTGUI_ADMIN_PASS
# env var set. During tests we don't want that side effect (it writes to
# cache/admin_password.txt inside the repo and spams stdout), so we pin a
# deterministic admin password before anything imports `config`.
os.environ.setdefault("LUNAWAVE_ADMIN_PASS", "test-admin-password-not-a-secret")
os.environ.setdefault("LUNAWAVE_BASE", str(REPO_ROOT))


@pytest.fixture
def tmp_base_dir(tmp_path, monkeypatch):
    """Isolated BASE_DIR-like tmp directory for tests that touch the filesystem."""
    monkeypatch.setenv("LUNAWAVE_BASE", str(tmp_path))
    return tmp_path


@pytest.fixture
async def db():
    """In-memory SQLite `cache.db.Database`, migrated and ready to use."""
    from cache.db import Database

    database = Database(db_path=Path(":memory:"))
    await database.init()
    yield database
    await database.close()


@pytest.fixture
async def memory_db():
    """SQLite in-memory — murah, cepat, tidak meninggalkan file."""
    import aiosqlite

    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    schema = (Path(__file__).parent.parent / "persistence" / "schema.sql").read_text(
        encoding="utf-8"
    )
    await conn.executescript(schema)
    yield conn
    await conn.close()

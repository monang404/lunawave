"""
Module: bootstrap.maintenance

Purpose:
    Unit tests for bootstrap.maintenance.

Responsibilities:
    - Test functionality and edge cases.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.state import PlayerStatus


@pytest.fixture(autouse=True)
def _reset_context():
    """Reset the module-level context singleton in place before/after each
    test (see tests/unit/test_main.py for why rebinding wouldn't work)."""
    import bootstrap.services as services

    services.context.__init__()
    yield
    services.context.__init__()


@pytest.mark.asyncio
async def test_schedule_db_maintenance_appends_task():
    from bootstrap.maintenance import schedule_db_maintenance
    from bootstrap.services import context

    context.repos = MagicMock()
    context.repos.tracks.evict_stale_tracks = AsyncMock(return_value=0)
    context.repos.sessions.cleanup_sessions = AsyncMock()

    schedule_db_maintenance()

    assert len(context.tasks) == 1
    assert context.tasks[0].get_name() == "db_maintenance"

    for t in context.tasks:
        t.cancel()
    await asyncio.gather(*context.tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_db_maintenance_runs_initial_eviction_and_cleanup():
    from bootstrap.maintenance import db_maintenance
    from bootstrap.services import context

    context.repos = MagicMock()
    context.repos.tracks.evict_stale_tracks = AsyncMock(return_value=3)
    context.repos.sessions.cleanup_sessions = AsyncMock()

    task = asyncio.create_task(db_maintenance())
    await asyncio.sleep(0.01)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

    context.repos.tracks.evict_stale_tracks.assert_awaited_once()
    context.repos.sessions.cleanup_sessions.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_mpv_watchdog_appends_task():
    from bootstrap.maintenance import start_mpv_watchdog
    from bootstrap.services import context

    context.mpv = MagicMock()
    context.state = MagicMock()

    start_mpv_watchdog()

    assert len(context.tasks) == 1
    assert context.tasks[0].get_name() == "mpv_watchdog"

    for t in context.tasks:
        t.cancel()
    await asyncio.gather(*context.tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_mpv_watchdog_sets_error_when_disconnected(monkeypatch):
    from bootstrap import maintenance
    from bootstrap.services import context

    context.mpv = MagicMock()
    context.mpv.is_available = True
    context.mpv.is_connected = False
    context.state = MagicMock()
    context.state.status = PlayerStatus.PLAYING

    # `mpv_watchdog` is an infinite `while True: await asyncio.sleep(10); ...`
    # loop. Rather than racing real timers, let the first sleep pass through
    # (so the loop body runs once and mutates state) and raise on the second
    # call to break out of the loop deterministically.
    call_count = {"n": 0}

    async def _sleep_then_stop(_seconds):
        call_count["n"] += 1
        if call_count["n"] > 1:
            raise asyncio.CancelledError()

    monkeypatch.setattr(maintenance.asyncio, "sleep", _sleep_then_stop)

    with pytest.raises(asyncio.CancelledError):
        await maintenance.mpv_watchdog()

    assert context.state.status == PlayerStatus.ERROR
    assert context.state.error_msg

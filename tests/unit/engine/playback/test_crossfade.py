"""
Module: tests.unit.engine.playback.test_crossfade

Purpose:
    Unit tests for engine.playback.crossfade -- sebelumnya modul ini punya
    nol test coverage (lihat implementation-plan.md Batch 3, item #9).

Responsibilities:
    - Verifikasi apply_crossfade_in mencapai volume target.
    - Verifikasi fade berhenti awal kalau status berubah (branch `break`).
    - Verifikasi cancellation tidak meninggalkan state korup.
    - Verifikasi check_crossfade_out (fade-out) di window terakhir.

Depends on:
    - engine.playback.crossfade
    - core.state

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from core.state import AppState, PlayerStatus
from engine.playback.crossfade import apply_crossfade_in, check_crossfade_out


def make_mpv():
    mpv = AsyncMock()
    mpv.set_volume = AsyncMock()
    return mpv


@pytest.mark.asyncio
async def test_apply_crossfade_in_reaches_target_volume():
    state = AppState()
    state.status = PlayerStatus.PLAYING
    state.volume = 80
    mpv = make_mpv()

    with patch_sleep():
        await apply_crossfade_in(mpv, state)

    # Panggilan pertama harus set_volume(0), panggilan terakhir harus
    # mencapai volume target (80).
    calls = [c.args[0] for c in mpv.set_volume.call_args_list]
    assert calls[0] == 0
    assert calls[-1] == 80


@pytest.mark.asyncio
async def test_apply_crossfade_in_stops_early_when_status_changes():
    """Branch `break` yang sudah ada -- kalau status berubah jadi bukan
    PLAYING/LOADING di tengah fade (mis. user pause/stop), fade harus
    berhenti dan tidak lanjut ramp ke volume penuh."""
    state = AppState()
    state.status = PlayerStatus.PLAYING
    state.volume = 100
    mpv = make_mpv()

    call_count = 0

    async def fake_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count == 3:
            state.status = PlayerStatus.PAUSED

    with patch("engine.playback.crossfade.asyncio.sleep", fake_sleep):
        await apply_crossfade_in(mpv, state)

    calls = [c.args[0] for c in mpv.set_volume.call_args_list]
    # Tidak boleh pernah mencapai volume penuh (100) karena fade berhenti awal.
    assert 100 not in calls
    # set_volume(0) di awal + beberapa step parsial sebelum berhenti.
    assert len(calls) < 11


@pytest.mark.asyncio
async def test_apply_crossfade_in_cancellation_does_not_corrupt_state():
    """Kalau task di-cancel di tengah fade, CancelledError harus propagate
    bersih (tidak ada try/except yang menelan-nya secara diam-diam) dan
    tidak ada volume "nyangkut" di angka aneh yang tidak konsisten."""
    state = AppState()
    state.status = PlayerStatus.PLAYING
    state.volume = 80
    mpv = make_mpv()

    task = asyncio.create_task(apply_crossfade_in(mpv, state))
    await asyncio.sleep(0)  # let it start and call set_volume(0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    # Volume terakhir yang di-set adalah nilai yang valid (bukan None/garbage),
    # dan tidak pernah melebihi volume target.
    calls = [c.args[0] for c in mpv.set_volume.call_args_list]
    assert all(0 <= v <= state.volume for v in calls)


@pytest.mark.asyncio
async def test_check_crossfade_out_fades_in_last_two_seconds():
    state = AppState()
    state.volume = 80
    mpv = make_mpv()

    await check_crossfade_out(mpv, state, remaining=1.0)

    mpv.set_volume.assert_awaited_once_with(40)


@pytest.mark.asyncio
async def test_check_crossfade_out_noop_outside_window():
    state = AppState()
    state.volume = 80
    mpv = make_mpv()

    await check_crossfade_out(mpv, state, remaining=5.0)

    mpv.set_volume.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_crossfade_out_noop_when_remaining_zero_or_negative():
    state = AppState()
    state.volume = 80
    mpv = make_mpv()

    await check_crossfade_out(mpv, state, remaining=0.0)
    await check_crossfade_out(mpv, state, remaining=-1.0)

    mpv.set_volume.assert_not_awaited()


def patch_sleep():
    return patch("engine.playback.crossfade.asyncio.sleep", AsyncMock())


from unittest.mock import patch  # noqa: E402  (used by patch_sleep helper above)

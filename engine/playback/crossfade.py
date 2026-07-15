"""
Module: engine.playback.crossfade

Purpose:
    Crossfade helpers untuk transisi halus antar track via MPV volume ramping.

Responsibilities:
    - Fade-in volume saat track baru mulai (apply_crossfade_in)
    - Fade-out volume saat track mendekati akhir (check_crossfade_out)

Depends on:
    - core.state
    - core.ports (AudioPlayerPort via mpv instance)

Subscribes to:
    None (dipanggil langsung oleh mode_ops)

Publishes:
    None

Thread Safety:
    Async-safe; tidak ada shared mutable state.
"""

import asyncio

from core.state import AppState, PlayerStatus


async def apply_crossfade_in(mpv, state: AppState):
    await mpv.set_volume(0)
    steps = 10
    for i in range(1, steps + 1):
        await asyncio.sleep(0.2)
        if state.status not in (PlayerStatus.PLAYING, PlayerStatus.LOADING):
            break
        vol = int(state.volume * (i / steps))
        await mpv.set_volume(vol)


async def check_crossfade_out(mpv, state: AppState, remaining: float):
    if remaining <= 2.0 and remaining > 0:
        fade_vol = max(0, int(state.volume * (remaining / 2.0)))
        await mpv.set_volume(fade_vol)

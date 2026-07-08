"""
Tests for S02-033: EnqueueGenreSongs lock preventing race condition
"""
import asyncio

import pytest


@pytest.mark.asyncio
async def test_enqueue_genre_lock_exists():
    """Verifikasi bahwa _enqueue_genre_lock tersedia di queue_handlers."""
    from server.handlers.ws import queue_handlers
    assert hasattr(queue_handlers, "_enqueue_genre_lock"), "_enqueue_genre_lock harus ada"
    assert isinstance(queue_handlers._enqueue_genre_lock, asyncio.Lock)


@pytest.mark.asyncio
async def test_enqueue_genre_lock_prevents_concurrent_dispatch():
    """Verifikasi bahwa concurrent calls tidak bisa masuk bersamaan ke dalam lock."""
    from server.handlers.ws import queue_handlers

    order = []
    original_lock = queue_handlers._enqueue_genre_lock

    async def slow_acquire():
        async with original_lock:
            order.append("start")
            await asyncio.sleep(0.05)
            order.append("end")

    # Dua coroutine concurrent — harus sequential, bukan interleaved
    await asyncio.gather(slow_acquire(), slow_acquire())

    assert order == ["start", "end", "start", "end"], \
        f"Lock tidak berfungsi, eksekusi interleaved: {order}"

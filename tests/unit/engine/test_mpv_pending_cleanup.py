"""
Tests for S02-037: MpvController._pending cleanup on CancelledError
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_pending_cleaned_on_timeout():
    """Verifikasi bahwa _pending di-pop saat TimeoutError."""
    from core.event_bus import EventBus
    from engine.mpv_controller import MpvController

    bus = EventBus()
    ctrl = MpvController(event_bus=bus)
    ctrl.is_connected = True
    ctrl._writer = MagicMock()
    ctrl._writer.write = MagicMock()
    ctrl._writer.drain = AsyncMock()

    # Simulasi wait_for yang timeout setelah future dibuat
    _original_send = ctrl._send_request.__func__ if hasattr(ctrl._send_request, '__func__') else None

    async def fake_wait_for(coro, timeout):
        if asyncio.isfuture(coro):
            coro.cancel()
        raise asyncio.TimeoutError()

    with patch("asyncio.wait_for", side_effect=fake_wait_for):
        result = await ctrl._send_request(["get_property", "time-pos"])

    assert result is None, "Harus return None saat timeout"
    assert len(ctrl._pending) == 0, "_pending harus kosong setelah TimeoutError"


@pytest.mark.asyncio
async def test_pending_cleaned_on_cancelled():
    """Verifikasi bahwa _pending di-pop dan CancelledError di-raise-ulang."""
    from core.event_bus import EventBus
    from engine.mpv_controller import MpvController

    bus = EventBus()
    ctrl = MpvController(event_bus=bus)
    ctrl.is_connected = True
    ctrl._writer = MagicMock()
    ctrl._writer.write = MagicMock()
    ctrl._writer.drain = AsyncMock()

    async def fake_wait_for(coro, timeout):
        if asyncio.isfuture(coro):
            coro.cancel()
        raise asyncio.CancelledError()

    with patch("asyncio.wait_for", side_effect=fake_wait_for):
        with pytest.raises(asyncio.CancelledError):
            await ctrl._send_request(["get_property", "time-pos"])

    # _pending harus kosong setelah CancelledError (S02-037)
    assert len(ctrl._pending) == 0, "_pending harus kosong setelah CancelledError"


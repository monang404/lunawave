"""
Module: adapters.mpv.observer

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import json

import structlog

from core.event_bus import EventBus
from core.events import (
    TrackDurationEvent,
    TrackEndedEvent,
    TrackPauseChangedEvent,
    TrackProgressEvent,
)
from core.task_utils import safe_create_task

logger = structlog.get_logger(__name__)


class MpvObserver:
    """Baca event dari MPV socket, publish ke EventBus sebagai DomainEvent."""

    def __init__(self, connection, ipc, event_bus: EventBus, room_id="default"):
        self._conn = connection
        self._ipc = ipc
        self._bus = event_bus
        self._room_id = room_id
        self._task = None
        self._last_progress_ts: float = 0.0

    async def start(self):
        if not self._task or self._task.done():
            self._task = safe_create_task(self._observe_loop(), name="mpv-observer")

    async def stop(self):
        if self._task:
            self._task.cancel()

    async def _observe_loop(self):
        """Event loop listener for mpv events (end-file, time-pos, etc)."""
        try:
            await asyncio.gather(
                self._ipc.send_command(["observe_property", 1, "time-pos"]),
                self._ipc.send_command(["observe_property", 2, "pause"]),
                self._ipc.send_command(["observe_property", 3, "duration"]),
            )

            while self._conn.is_connected:
                try:
                    if not self._conn.reader:
                        break
                    line = await self._conn.reader.readline()
                    if not line:
                        break
                    msg = json.loads(line.decode())
                    await self._handle_event(msg)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                except (ConnectionError, OSError, asyncio.IncompleteReadError):
                    break
        finally:
            self._conn.is_connected = False
            self._ipc.cancel_all_pending()
            logger.warning("mpv observer loop ended — connection lost.")

            if not getattr(self._conn, "shutting_down", False):
                # Coba reconnect ke mpv yang mungkin masih hidup (misal socket terputus sesaat)
                reconnected = False
                for attempt in range(3):
                    backoff = 2**attempt  # 1s, 2s, 4s
                    logger.info(
                        f"Mencoba reconnect ke mpv (attempt {attempt + 1}/3) dalam {backoff}s..."
                    )
                    await asyncio.sleep(backoff)
                    if getattr(self._conn, "shutting_down", False):
                        break
                    try:
                        connected = await self._conn.reconnect()
                        if connected:
                            self._task = safe_create_task(self._observe_loop(), name="mpv-observer")
                            logger.info(f"Reconnect ke mpv berhasil (attempt {attempt + 1})")
                            reconnected = True
                            break
                    except (ConnectionError, OSError, FileNotFoundError, Exception) as e:
                        logger.warning(f"Reconnect attempt {attempt + 1} gagal: {e}")

                if not reconnected:
                    logger.error("Semua percobaan reconnect ke mpv gagal.")
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self._bus.publish(TrackEndedEvent(reason="error")))
                    except RuntimeError:
                        pass

    async def _handle_event(self, msg: dict):
        if "request_id" in msg:
            fut = self._ipc.pop_pending(msg["request_id"])
            if fut and not fut.done():
                fut.set_result(msg.get("data"))
            return

        event = msg.get("event")
        if event == "property-change":
            name = msg.get("name")
            data = msg.get("data")
            if name == "time-pos" and isinstance(data, (int, float)):
                import time as _time

                _now = _time.monotonic()
                # Throttle: publish maksimal 1× per detik untuk hemat CPU/baterai.
                if _now - self._last_progress_ts >= 1.0:
                    self._last_progress_ts = _now
                    await self._bus.publish(TrackProgressEvent(position=float(data)))
            elif name == "pause":
                await self._bus.publish(TrackPauseChangedEvent(is_paused=bool(data)))
            elif name == "duration" and isinstance(data, (int, float)):
                await self._bus.publish(TrackDurationEvent(duration=float(data)))
        elif event == "end-file":
            reason = msg.get("reason", "")
            if reason in ("eof", "stop", "error"):
                await self._bus.publish(TrackEndedEvent(reason=reason))

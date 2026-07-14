"""
Module: adapters.mpv

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

from adapters.mpv.connection import MpvConnection
from adapters.mpv.ipc import MpvIPC
from adapters.mpv.observer import MpvObserver


class MpvController:
    """
    Facade — API publik identik dengan engine/mpv_controller.py lama.
    Tidak ada kode lain yang perlu berubah.
    """

    def __init__(
        self,
        socket_path: str = None,  # type: ignore
        tcp_port: str = None,  # type: ignore
        event_bus=None,
        room_id: str = "default",
    ):
        self._conn = MpvConnection(socket_path, tcp_port)
        self._ipc = MpvIPC(self._conn)

        # Injected per-room bus (fallback ke global jika belum direfactor)
        if event_bus is None:
            from core.event_bus import bus as _global_bus

            event_bus = _global_bus

        self._observer = MpvObserver(self._conn, self._ipc, event_bus, room_id)
        self._room_id = room_id

    @property
    def is_connected(self):
        return self._conn.is_connected

    async def connect(self):
        connected = await self._conn.connect()
        if connected:
            await self._observer.start()
        return connected

    async def play(self, url_or_path: str):
        if not self.is_connected:
            return
        await self._ipc.send_command(["loadfile", url_or_path, "replace"])

    async def pause(self):
        if not self.is_connected:
            return
        await self._ipc.set_property("pause", True)

    async def resume(self):
        if not self.is_connected:
            return
        await self._ipc.set_property("pause", False)

    async def toggle_pause(self):
        if not self.is_connected:
            return
        await self._ipc.send_command(["cycle", "pause"])

    async def stop(self):
        if not self.is_connected:
            return
        await self._ipc.send_command(["stop"])

    async def seek(self, seconds: float):
        if not self.is_connected:
            return
        await self._ipc.send_command(["seek", seconds, "absolute"])

    async def set_volume(self, vol: int):
        if not self.is_connected:
            return
        await self._ipc.set_property("volume", max(0, min(150, vol)))

    async def get_position(self) -> float:
        if not self.is_connected:
            return 0.0
        val = await self._ipc.get_property("time-pos")
        return val if val else 0.0

    async def get_duration(self) -> float:
        if not self.is_connected:
            return 0.0
        val = await self._ipc.get_property("duration")
        return val if val else 0.0

    async def close(self):
        await self._observer.stop()
        await self._conn.disconnect()

"""
Module: adapters.mpv.connection

Purpose:
    Manages the raw socket connection to the MPV media player.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.exceptions

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
import os
import shutil

import structlog

from config import MPV_SOCKET
from core.exceptions import MpvConnectionError

logger = structlog.get_logger(__name__)


class MpvConnection:
    """Handle buka/tutup/reconnect socket ke MPV. Tidak tahu tentang playback."""

    def __init__(self, socket_path: str = None, tcp_port: str = None):  # type: ignore
        self.socket_path = socket_path or MPV_SOCKET
        self.tcp_port = tcp_port or os.environ.get("YT_PLAYER_MPV_PORT", "12345")
        self._reader = None
        self._writer = None
        self.is_connected = False
        self._reconnect_lock = asyncio.Lock()
        self._mpv_process = None
        self.shutting_down = False

    @property
    def reader(self):
        return self._reader

    @property
    def writer(self):
        return self._writer

    async def connect(self) -> bool:
        """Connect ke MPV socket. Return True jika sukses."""
        async with self._reconnect_lock:
            if self.is_connected:
                return True
            return await self._do_connect()

    async def _do_connect(self) -> bool:
        ytdl_path = shutil.which("yt-dlp")
        ytdl_arg = f"--script-opts=ytdl_hook-ytdl_path={ytdl_path}" if ytdl_path else ""

        common_args = [
            "--no-video",
            "--idle",
            "--ytdl-format=bestaudio/best",
            "--audio-pitch-correction=yes",
            "--cache=yes",
            "--demuxer-readahead-secs=20",
            "--demuxer-max-bytes=30MiB",
            "--cache-pause=yes",
            "--network-timeout=15",
        ]

        if os.name == "nt":
            cmd = ["mpv"] + common_args + [f"--input-ipc-server=tcp://127.0.0.1:{self.tcp_port}"]
            if ytdl_arg:
                cmd.insert(1, ytdl_arg)
        else:
            os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
            if os.path.exists(self.socket_path):
                try:
                    os.remove(self.socket_path)
                except OSError:
                    pass
            cmd = ["mpv"] + common_args + [f"--input-ipc-server={self.socket_path}"]
            if ytdl_arg:
                cmd.insert(1, ytdl_arg)

        try:
            self._mpv_process = await asyncio.create_subprocess_exec(  # type: ignore
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                stdin=asyncio.subprocess.DEVNULL,
            )
            if os.name != "nt":
                # Poll sampai socket tersedia, max 5 detik
                for _ in range(50):
                    await asyncio.sleep(0.1)
                    if os.path.exists(self.socket_path):
                        break
            else:
                await asyncio.sleep(1.0)
        except OSError as e:
            logger.error(f"Failed to spawn mpv process: {e}")

        for attempt in range(10):
            try:
                if os.name == "nt":
                    self._reader, self._writer = await asyncio.open_connection(  # type: ignore
                        "127.0.0.1", int(self.tcp_port)
                    )
                else:
                    self._reader, self._writer = await asyncio.open_unix_connection(  # type: ignore
                        self.socket_path
                    )

                self.is_connected = True
                self.shutting_down = False
                if os.name != "nt":
                    try:
                        import stat

                        os.chmod(self.socket_path, stat.S_IRUSR | stat.S_IWUSR)
                    except OSError:
                        pass
                logger.info(f"Connected to mpv (attempt {attempt + 1})")
                return True
            except MpvConnectionError:
                raise
            except (ConnectionError, OSError, FileNotFoundError):
                await asyncio.sleep(0.5)
        raise MpvConnectionError(
            f"Cannot connect to mpv socket after 10 attempts (TCP: {os.environ.get('YT_PLAYER_MPV_PORT', 'N/A')}, Unix: {self.socket_path})"
        )

    async def disconnect(self):
        self.shutting_down = True
        self.is_connected = False

        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError:
                pass

        if self._mpv_process:
            try:
                self._mpv_process.terminate()
                try:
                    await asyncio.wait_for(self._mpv_process.wait(), timeout=1.0)
                except TimeoutError:
                    self._mpv_process.kill()
            except OSError:
                pass

    async def reconnect(self) -> bool:
        async with self._reconnect_lock:
            if self.is_connected:
                return True
            # We don't call disconnect() here because we might want to just retry socket connection
            # But in do_connect it restarts the process anyway.
            # For simplicity, just disconnect and connect.
            self.is_connected = False
            return await self._do_connect()

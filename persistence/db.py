"""
Module: persistence.db

Purpose:
    Manages the SQLite database connection lifecycle and initialization.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

from pathlib import Path

import aiosqlite
import structlog

from config import DB_PATH

logger = structlog.get_logger(__name__)


class DatabaseConnection:
    """Handle koneksi SQLite saja. Tidak tahu domain (track, artist, dll.)."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._conn = None

    @property
    def conn(self):
        return self._conn

    async def init(self, schema_path: Path):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)  # type: ignore
        self._conn.row_factory = aiosqlite.Row  # type: ignore
        await self._conn.execute("PRAGMA journal_mode=WAL")  # type: ignore
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()
        await self._conn.executescript(schema_sql)  # type: ignore

    async def close(self):
        if self._conn:
            # Simpan referensi thread worker SEBELUM close(), karena setelah
            # close() self._conn sudah None.
            worker_thread = getattr(self._conn, "_thread", None)
            await self._conn.close()
            self._conn = None

            # ROOT-CAUSE-FIX (zombie thread): aiosqlite.Connection.close()
            # menganggap selesai begitu future dari stop() ter-resolve, tapi
            # future itu di-resolve via call_soon_threadsafe() DI DALAM worker
            # thread, SEBELUM thread itu sendiri sempat break dari loop-nya
            # (lihat _connection_worker_thread: set_result dulu baru cek
            # sentinel & break). Jadi ada window kecil di mana close() sudah
            # return tapi OS thread masih hidup -- inilah yang bikin
            # '_connection_worker_thread' nyangkut jadi zombie non-daemon
            # thread di akhir test run dan memicu force-exit CI.
            # Join eksplisit di sini memberi jaminan nyata bahwa thread sudah
            # benar-benar terminate sebelum close() return ke caller.
            if worker_thread is not None and worker_thread.is_alive():
                import asyncio

                await asyncio.sleep(0.01)

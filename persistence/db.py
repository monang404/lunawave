"""
Module: persistence.db

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import aiosqlite
import structlog
from pathlib import Path
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
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        await self._conn.executescript(schema_sql)

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

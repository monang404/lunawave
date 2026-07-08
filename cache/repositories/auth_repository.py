import time

import structlog

from core.ports import SessionRepositoryPort

logger = structlog.get_logger(__name__)

class AuthRepository(SessionRepositoryPort):
    def __init__(self, db_conn):
        self._conn = db_conn

    async def create_session(self, token: str, expires_at: int) -> None:
        if not self._conn: return
        await self._conn.execute(
            "INSERT INTO sessions (token, expires_at) VALUES (?, ?)",
            (token, expires_at)
        )
        await self._conn.commit()

    async def verify_session(self, token: str) -> bool:
        if not self._conn: return False
        now = int(time.time())
        async with self._conn.execute(
            "SELECT expires_at FROM sessions WHERE token = ?", (token,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["expires_at"] > now:
                return True
            return False

    async def delete_session(self, token: str) -> None:
        if not self._conn: return
        await self._conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        await self._conn.commit()

    async def cleanup_sessions(self) -> None:
        if not self._conn: return
        now = int(time.time())
        await self._conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
        await self._conn.commit()

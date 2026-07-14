"""
Module: persistence.session_repo

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import time


class SessionRepository:
    def __init__(self, conn):
        self._conn = conn

    async def create_session(self, token: str, expires_at: int):
        await self._conn.execute(
            "INSERT INTO sessions (token, expires_at) VALUES (?, ?)", (token, expires_at)
        )
        await self._conn.commit()

    async def verify_session(self, token: str) -> bool:
        now = int(time.time())
        async with self._conn.execute(
            "SELECT expires_at FROM sessions WHERE token = ?", (token,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["expires_at"] > now:
                return True
            if row:
                await self.delete_session(token)
            return False

    async def delete_session(self, token: str):
        await self._conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        await self._conn.commit()

    async def cleanup_sessions(self):
        now = int(time.time())
        await self._conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
        await self._conn.commit()

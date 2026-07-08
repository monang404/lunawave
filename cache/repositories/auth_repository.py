import time
import structlog
from core.ports import SessionRepositoryPort

logger = structlog.get_logger(__name__)

class AuthRepository(SessionRepositoryPort):
    def __init__(self, pool):
        self.pool = pool

    async def create_session(self, token: str, expires_at: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO sessions (token, expires_at) VALUES (?, ?)",
                (token, expires_at)
            )
            await conn.commit()

    async def verify_session(self, token: str) -> bool:
        now = int(time.time())
        async with self.pool.acquire() as conn:
            async with conn.execute(
                "SELECT expires_at FROM sessions WHERE token = ?", (token,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row["expires_at"] > now:
                    return True
                return False

    async def delete_session(self, token: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            await conn.commit()

    async def cleanup_sessions(self) -> None:
        now = int(time.time())
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            await conn.commit()

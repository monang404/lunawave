import time

import pytest

from persistence.session_repo import SessionRepository


@pytest.mark.asyncio
async def test_session_repo_delete_all():
    import aiosqlite

    async with aiosqlite.connect(":memory:") as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(
            """CREATE TABLE sessions (
                token TEXT PRIMARY KEY,
                expires_at INTEGER NOT NULL
            )"""
        )
        repo = SessionRepository(conn)

        now = int(time.time())
        await repo.create_session("token1", now + 3600)
        await repo.create_session("token2", now + 3600)

        assert await repo.verify_session("token1")
        assert await repo.verify_session("token2")

        await repo.delete_all_sessions()

        assert not await repo.verify_session("token1")
        assert not await repo.verify_session("token2")

import pytest
from cache.db import Database

@pytest.mark.asyncio
async def test_db_has_is_favorite_index(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    await db.init()

    # Query sqlite_master to verify the index exists
    async with db.conn.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name='idx_is_favorite'") as cursor:
        row = await cursor.fetchone()

    assert row is not None, "Index idx_is_favorite should exist"
    assert "is_favorite = 1" in row["sql"], "Should be a partial index"

    await db.close()

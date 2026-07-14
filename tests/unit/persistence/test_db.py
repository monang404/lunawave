"""
Module: tests.unit.persistence.test_db

Purpose:
    Unit tests for database initialization and connection handling.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - persistence

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""


async def test_init_is_idempotent_when_called_twice_on_a_file_backed_db(tmp_path):
    from persistence import Database

    path = tmp_path / "idempotent.db"
    database = Database(db_path=path)
    await database.init()
    await database.close()

    # Re-opening and re-running migrations must not raise.
    database2 = Database(db_path=path)
    await database2.init()

    # Concrete assertion: verify that the database connection works and schema exists
    async with database2.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ) as cursor:
        tables = [row[0] async for row in cursor]
        assert len(tables) > 0, "Database should contain tables after init"

    await database2.close()

"""
Module: tests.unit.persistence.test_db

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
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
    await database2.close()

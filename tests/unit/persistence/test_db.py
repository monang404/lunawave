"""
Module: tests.unit.persistence.test_db

Purpose:
    Unit tests for database connection lifecycle: initialization,
    idempotent re-init, thread-safe close, and the songs table migration.
    These all live in `persistence.db.DatabaseConnection` (extracted from
    the old `Database` God Facade in PATCH T2.2a; the facade itself was
    removed in PATCH T2.2e), so we test that class directly.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - persistence.db

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "persistence" / "schema.sql"


async def test_init_is_idempotent_when_called_twice_on_a_file_backed_db(tmp_path):
    from persistence.db import DatabaseConnection

    path = tmp_path / "idempotent.db"
    conn_mgr = DatabaseConnection(path)
    await conn_mgr.init(SCHEMA_PATH)
    await conn_mgr.close()

    # Re-opening and re-running migrations must not raise.
    conn_mgr2 = DatabaseConnection(path)
    await conn_mgr2.init(SCHEMA_PATH)

    # Concrete assertion: verify that the database connection works and schema exists
    async with conn_mgr2.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ) as cursor:
        tables = [row[0] async for row in cursor]
        assert len(tables) > 0, "Database should contain tables after init"

    await conn_mgr2.close()


async def test_close_joins_connection_worker_thread(tmp_path):
    """PATCH-2026-07-16-001 regression: close() must actually join the
    aiosqlite connection worker thread, not just sleep(0.01) and hope. A
    thread left alive after close() is a non-daemon zombie thread that
    prevents the process from exiting cleanly (root cause of the CI hang
    investigated in implementation-plan.md Batch 0)."""
    from persistence.db import DatabaseConnection

    path = tmp_path / "close_joins_thread.db"
    conn_mgr = DatabaseConnection(path)
    await conn_mgr.init(SCHEMA_PATH)

    worker_thread = conn_mgr.conn._thread
    assert worker_thread.is_alive()

    await conn_mgr.close()

    assert not worker_thread.is_alive()


async def test_songs_migration_recovers_collaboration_song_on_old_schema(tmp_path):
    """PATCH-2026-07-16-048 regression: a pre-existing DB created under the
    old schema (youtube_id globally UNIQUE) must be migrated in-place to a
    composite UNIQUE(artist_id, youtube_id), and any collaboration song that
    was already present for one artist must remain queryable afterwards
    (the migration itself doesn't need to resurrect data lost by the old
    export tool — that's covered by the export tool's own regression test —
    but it must not lose or corrupt what is already in the DB, and it must
    allow a second artist to be linked to the same video going forward)."""
    import sqlite3

    from persistence.db import DatabaseConnection

    path = tmp_path / "old_schema.db"

    # Build a DB with the OLD schema (global UNIQUE on youtube_id) and one
    # song already present for "Peterpan".
    raw_conn = sqlite3.connect(path)
    raw_conn.execute(
        """
        CREATE TABLE artists (
            id INTEGER PRIMARY KEY,
            nama TEXT NOT NULL,
            kategori TEXT,
            tahun_aktif TEXT
        )
        """
    )
    raw_conn.execute(
        """
        CREATE TABLE songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_id INTEGER,
            judul TEXT NOT NULL,
            youtube_id TEXT UNIQUE NOT NULL,
            duration INTEGER DEFAULT 0,
            FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
        )
        """
    )
    raw_conn.execute("INSERT INTO artists (id, nama) VALUES (1, 'Peterpan')")
    raw_conn.execute(
        "INSERT INTO songs (artist_id, judul, youtube_id, duration) VALUES (1, 'Separuh Aku', 'tstwxIh6xJw', 240)"
    )
    raw_conn.commit()
    raw_conn.close()

    conn_mgr = DatabaseConnection(path)
    await conn_mgr.init(SCHEMA_PATH)

    # Old data survived the migration.
    async with conn_mgr.conn.execute(
        "SELECT artist_id, judul, duration FROM songs WHERE youtube_id = 'tstwxIh6xJw'"
    ) as cursor:
        rows = await cursor.fetchall()
    assert [dict(r) for r in rows] == [{"artist_id": 1, "judul": "Separuh Aku", "duration": 240}]

    # The constraint is now per-artist: a second artist can own the same video_id.
    await conn_mgr.conn.execute("INSERT INTO artists (id, nama) VALUES (2, 'NOAH')")
    await conn_mgr.conn.execute(
        "INSERT INTO songs (artist_id, judul, youtube_id, duration) VALUES (2, 'Separuh Aku', 'tstwxIh6xJw', 240)"
    )
    await conn_mgr.conn.commit()

    async with conn_mgr.conn.execute(
        "SELECT artist_id FROM songs WHERE youtube_id = 'tstwxIh6xJw' ORDER BY artist_id"
    ) as cursor:
        owning_artists = [row[0] async for row in cursor]
    assert owning_artists == [1, 2]

    await conn_mgr.close()

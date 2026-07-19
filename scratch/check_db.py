"""
Module: scratch.check_db

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import sqlite3
from pathlib import Path

from persistence import Repositories
from core.state import TrackInfo


async def main():
    repos = Repositories(Path("data/lunawave.db"))
    await repos.init()

    # Check current tracks with local_path
    conn = sqlite3.connect("data/lunawave.db")
    rows = conn.execute(
        "SELECT video_id, title, local_path FROM tracks WHERE local_path IS NOT NULL"
    ).fetchall()
    print("Currently in DB:", rows)

    # Try inserting a test track
    t = TrackInfo(video_id="test1", title="t1", artist="a1", duration=10)
    await repos.tracks.upsert_track(t, local_path="test_local_path.mp3")

    # Verify insertion
    row = conn.execute("SELECT local_path FROM tracks WHERE video_id='test1'").fetchone()
    print("Test insert result:", row)

    await repos.close()


if __name__ == "__main__":
    asyncio.run(main())

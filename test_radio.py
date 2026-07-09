from pathlib import Path
import asyncio
from core.state import AppState
from engine.radio_engine import RadioMode
from cache.db import Database
import logging

logging.basicConfig(level=logging.DEBUG)

async def main():
    db = Database(Path("data/lunawave.db"))
    await db.init()
    
    state = AppState()
    radio = RadioMode(None, state, db)
    
    print("Testing _ensure_artists_loaded...")
    try:
        await radio._ensure_artists_loaded()
        print(f"Loaded artists: {len(radio._seed_artists)}")
    except Exception as e:
        print(f"Error in _ensure_artists_loaded: {e}")

    print("\nTesting _gather_batch...")
    try:
        tracks = await radio._gather_batch(max_artists=2)
        print(f"Gathered {len(tracks)} tracks")
        for t in tracks:
            print(f"- {t.title} by {t.artist}")
    except Exception as e:
        print(f"Error in _gather_batch: {e}")
        
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())

"""
Module: server.handlers.ws_download

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import os
import re
from pathlib import Path

import structlog

from core.command_bus import CMD_DOWNLOAD, command_bus
from server.serializers import dict_to_track, track_to_dict
from services.discover_service import DiscoverService

logger = structlog.get_logger(__name__)


async def handle_download_command(action: str, data: dict, db, manager, state):
    if action == "download":
        track = dict_to_track(data) if data else None
        await command_bus.execute(CMD_DOWNLOAD, track)

    elif action == "delete_download":
        track = dict_to_track(data) if data else None
        if track and track.video_id:
            db_track = await db.get_track(track.video_id)
            if db_track and db_track.local_path:
                # Hapus file utama yang terdaftar di DB (bisa berupa downloads/ atau cache/mp3/ lama)
                if os.path.exists(db_track.local_path):
                    try:
                        os.remove(db_track.local_path)
                    except Exception as e:
                        logger.error(f"Gagal menghapus file lokal {db_track.local_path}: {e}")

                # Fallback legacy: hapus juga dari folder downloads jika dulu file tersimpan ganda
                safe_artist = re.sub(r'[\\/*?:"<>|]', "", db_track.artist)
                safe_title = re.sub(r'[\\/*?:"<>|]', "", db_track.title)
                user_path = Path("downloads") / f"{safe_artist} - {safe_title}.mp3"
                if user_path.exists() and str(user_path) != db_track.local_path:
                    try:
                        os.remove(str(user_path))
                    except:
                        pass

                # Update DB
                db_track.local_path = None
                await db.set_local_path(db_track.video_id, None)

                # Update current state if playing this track
                if state.current_track and state.current_track.video_id == db_track.video_id:
                    state.current_track.local_path = None
                    from server.serializers import state_to_dict

                    await manager.broadcast({"type": "state", "data": state_to_dict(state)})

                # Update discover
                ds = DiscoverService(db)
                recent, cached, featured_artists, featured_genres = await asyncio.gather(
                    ds.get_recent(15),
                    ds.get_cached(15),
                    ds.get_featured_artists(100),
                    ds.get_featured_genres(100),
                )
                await manager.broadcast(
                    {
                        "type": "discover_data",
                        "data": {
                            "recent": [track_to_dict(t) for t in recent],
                            "cached_tracks": [track_to_dict(t) for t in cached],
                            "featured_artists": featured_artists,
                            "featured_genres": featured_genres,
                        },
                    }
                )
                await manager.broadcast(
                    {"type": "log", "data": f"Unduhan dihapus: {db_track.title}"}
                )

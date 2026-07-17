"""
Module: server.handlers.ws_discovery

Purpose:
    WebSocket handler for processing discovery and search commands.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - server.serializers

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
import json

from server.serializers import track_to_dict
from services.discover_service import DiscoverService


async def handle_discovery_command(action: str, data: dict, ytdlp, db, ws):
    if action == "search":
        query = data.get("query", "").strip()
        if query:
            results = await ytdlp.search(query, max_results=10)
            await ws.send_str(
                json.dumps(
                    {
                        "type": "search_results",
                        "data": [track_to_dict(t) for t in results],
                    },
                    ensure_ascii=False,
                )
            )

    elif action == "discover":
        ds = DiscoverService(db)
        (
            recent,
            favorites,
            cached,
            featured_artists,
            featured_genres,
            for_you,
            unheard,
            genre_affinity,
            taste_spectrum,
        ) = await asyncio.gather(
            ds.get_recent(15),
            ds.get_favorites(15),
            ds.get_cached(15),
            ds.get_featured_artists(100),
            ds.get_featured_genres(100),
            ds.get_for_you(15),
            ds.get_unheard(15),
            ds.get_genre_affinity(15),
            ds.get_taste_spectrum(),
        )
        await ws.send_str(
            json.dumps(
                {
                    "type": "discover_data",
                    "data": {
                        "recent": [track_to_dict(t) for t in recent],
                        "favorites": [track_to_dict(t) for t in favorites],
                        "cached_tracks": [track_to_dict(t) for t in cached],
                        "featured_artists": featured_artists,
                        "featured_genres": featured_genres,
                        "for_you": for_you,
                        "unheard": unheard,
                        "genre_affinity_genre": genre_affinity["genre"],
                        "genre_affinity_artists": genre_affinity["artists"],
                        "taste_spectrum": taste_spectrum,
                    },
                },
                ensure_ascii=False,
            )
        )

    elif action == "get_artist_detail":
        # NOTE (PATCH-2026-07-17-070): this action is implemented and ready,
        # but it is UNREACHABLE until "get_artist_detail" is added to
        # DISCOVERY_CMDS in server/handlers/websocket.py — that file is
        # governance-restricted (AI_CONTEXT.md "tidak boleh disentuh tanpa
        # izin eksplisit") and was intentionally NOT touched in this patch.
        # See docs/PATCHLOG.md PATCH-2026-07-17-070 for the one-line change
        # needed before this branch can ever be dispatched to.
        ds = DiscoverService(db)
        artist = data.get("artist", "").strip()
        detail = await ds.get_artist_detail(artist) if artist else None
        await ws.send_str(
            json.dumps(
                {
                    "type": "artist_detail",
                    "data": detail,
                },
                ensure_ascii=False,
            )
        )

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
        recent, favorites, cached, featured_artists, featured_genres = await asyncio.gather(
            ds.get_recent(15),
            ds.get_favorites(15),
            ds.get_cached(15),
            ds.get_featured_artists(100),
            ds.get_featured_genres(100),
        )
        await ws.send_str(
            json.dumps(
                {
                    "type": "discover_data",
                    "data": {
                        "recent": [track_to_dict(t) for t in recent],
                        "cached_tracks": [track_to_dict(t) for t in cached],
                        "featured_artists": featured_artists,
                        "featured_genres": featured_genres,
                    },
                },
                ensure_ascii=False,
            )
        )

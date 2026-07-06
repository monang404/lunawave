import json
import re
from core.ws_actions import WSAction
from server.handlers.ws.registry import register_ws_handler
from server.services.discover_service import DiscoverService

VIDEO_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{11}$")

from core.constants import (
    DISCOVER_RECENT_LIMIT,
    DISCOVER_FAVORITES_LIMIT,
    DISCOVER_CACHED_LIMIT,
    DISCOVER_FEATURED_ARTISTS_LIMIT,
    DISCOVER_FEATURED_GENRES_LIMIT
)

async def _build_discover_payload(db):
    ds = DiscoverService(db)
    recent = await ds.get_recent(DISCOVER_RECENT_LIMIT)
    favorites = await ds.get_favorites(DISCOVER_FAVORITES_LIMIT)
    cached = await ds.get_cached(DISCOVER_CACHED_LIMIT)
    featured_artists = await ds.get_featured_artists(DISCOVER_FEATURED_ARTISTS_LIMIT)
    featured_genres = await ds.get_featured_genres(DISCOVER_FEATURED_GENRES_LIMIT)
    return {
        "type": "discover_data",
        "data": {
            "recent": [t.to_dict() for t in recent],
            "favorites": [t.to_dict() for t in favorites],
            "cached_tracks": [t.to_dict() for t in cached],
            "featured_artists": featured_artists,
            "featured_genres": featured_genres
        }
    }

async def broadcast_discover_data(manager, db):
    payload = await _build_discover_payload(db)
    await manager.broadcast(payload)

@register_ws_handler(WSAction.SEARCH)
async def _handle_search(data, ws, state, ytdlp, manager, db, command_bus):
    query = data.get("query", "").strip()
    try:
        max_results = min(max(1, int(data.get("max_results", 10))), 50)
    except (ValueError, TypeError):
        max_results = 10

    if query:
        results = await ytdlp.search(query, max_results=max_results)
        await ws.send_str(json.dumps({
            "type": "search_results",
            "data": [t.to_dict() for t in results],
        }, ensure_ascii=False))

@register_ws_handler(WSAction.DISCOVER)
async def _handle_discover(data, ws, state, ytdlp, manager, db, command_bus):
    payload = await _build_discover_payload(db)
    await ws.send_str(json.dumps(payload, ensure_ascii=False))

@register_ws_handler(WSAction.TOGGLE_FAVORITE)
async def _handle_toggle_favorite(data, ws, state, ytdlp, manager, db, command_bus):
    video_id = data.get("video_id")
    set_favorite = data.get("set_favorite")

    if video_id and VIDEO_ID_REGEX.match(str(video_id)):
        if set_favorite is not None:
            target = 1 if set_favorite else 0
            await db.conn.execute("UPDATE tracks SET is_favorite = ? WHERE video_id = ?", (target, video_id))
            await db.conn.commit()
            is_fav = target
        else:
            is_fav = await db.toggle_favorite(video_id)

        await ws.send_str(json.dumps({
            "type": "favorite_status",
            "data": {
                "video_id": video_id,
                "is_favorite": bool(is_fav)
            }
        }, ensure_ascii=False))

        if state.current_track and state.current_track.video_id == video_id:
            state.current_track.is_favorite = is_fav
            await manager.broadcast({
                "type": "state",
                "data": state.to_dict()
            })

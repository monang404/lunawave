from core.commands import (
    PlayTrackCommand,
    QueueAddCommand,
    QueueRemoveCommand,
    QueueReorderCommand,
    QueueReplaceCommand,
    QueueSelectCommand,
    SetModeCommand,
)
from core.state import PlaybackMode, TrackInfo
from core.ws_actions import WSAction
from server.handlers.ws.registry import register_ws_handler


@register_ws_handler(WSAction.QUEUE_SELECT)
async def _handle_queue_select(data, ws, state, ytdlp, manager, db, command_bus):
    try:
        index = max(0, int(data.get("index", 0)))
        await command_bus.execute(QueueSelectCommand(index=index))
    except (ValueError, TypeError):
        pass

@register_ws_handler(WSAction.QUEUE_REMOVE)
async def _handle_queue_remove(data, ws, state, ytdlp, manager, db, command_bus):
    try:
        index = max(0, int(data.get("index", 0)))
        await command_bus.execute(QueueRemoveCommand(index=index))
    except (ValueError, TypeError):
        pass

@register_ws_handler(WSAction.QUEUE_ADD)
async def _handle_queue_add(data, ws, state, ytdlp, manager, db, command_bus):
    track = TrackInfo.from_dict(data)
    if track:
        await command_bus.execute(QueueAddCommand(track=track))

@register_ws_handler(WSAction.QUEUE_REORDER)
async def _handle_queue_reorder(data, ws, state, ytdlp, manager, db, command_bus):
    try:
        from_idx = max(0, int(data.get("from_index", 0)))
        to_idx = max(0, int(data.get("to_index", 0)))
        await command_bus.execute(QueueReorderCommand(from_index=from_idx, to_index=to_idx))
    except (ValueError, TypeError):
        pass

@register_ws_handler(WSAction.ENQUEUE_ARTIST_SONGS)
async def _handle_enqueue_artist_songs(data, ws, state, ytdlp, manager, db, command_bus):
    artist_name = data.get("artist")
    if artist_name:
        songs = await db.get_artist_songs_strict(artist=artist_name, limit=10)
        if songs:
            await db.increment_artist_click(artist_name)
            first_track, rest_tracks = songs[0], songs[1:]
            await command_bus.execute(QueueReplaceCommand(tracks=rest_tracks))
            await command_bus.execute(PlayTrackCommand(track=first_track))

import asyncio as _asyncio

_enqueue_genre_lock = _asyncio.Lock()

@register_ws_handler(WSAction.ENQUEUE_GENRE_SONGS)
async def _handle_enqueue_genre_songs(data, ws, state, ytdlp, manager, db, command_bus):
    genre_name = data.get("genre")
    if genre_name:
        await db.increment_genre_click(genre_name)
        songs = await db.get_genre_songs(genre_name, total_limit=12, max_per_artist=3)
        if songs:
            async with _enqueue_genre_lock:
                # Tiga dispatch ini harus atomik: tidak boleh ada WS event lain
                # yang menyela di antara SetMode → Replace → Select (S02-033)
                await command_bus.execute(SetModeCommand(mode=PlaybackMode.QUEUE))
                await command_bus.execute(QueueReplaceCommand(tracks=songs))
                await command_bus.execute(QueueSelectCommand(index=0))


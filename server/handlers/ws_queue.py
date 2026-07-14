"""
Module: server.handlers.ws_queue

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

from core.command_bus import (
    CMD_PLAY_TRACK,
    CMD_QUEUE_ADD,
    CMD_QUEUE_REMOVE,
    CMD_QUEUE_REORDER,
    CMD_QUEUE_REPLACE,
    CMD_QUEUE_SELECT,
    CMD_SET_MODE,
    command_bus,
)
from core.state import PlaybackMode
from server.serializers import dict_to_track


async def handle_queue_command(action: str, data: dict, db):
    if action == "queue_select":
        index = data.get("index", 0)
        await command_bus.execute(CMD_QUEUE_SELECT, int(index))

    elif action == "queue_remove":
        index = data.get("index", 0)
        await command_bus.execute(CMD_QUEUE_REMOVE, int(index))

    elif action == "queue_add":
        track = dict_to_track(data)
        if track:
            await command_bus.execute(CMD_QUEUE_ADD, track)

    elif action == "queue_reorder":
        from_idx = int(data.get("from_index", 0))
        to_idx = int(data.get("to_index", 0))
        await command_bus.execute(CMD_QUEUE_REORDER, {"from_index": from_idx, "to_index": to_idx})

    elif action == "enqueue_artist_songs":
        artist_name = data.get("artist")
        if artist_name:
            songs = await db.get_artist_songs_strict(artist=artist_name, limit=10)
            if songs:
                await db.increment_artist_click(artist_name)
                first_track, rest_tracks = songs[0], songs[1:]
                await command_bus.execute(CMD_QUEUE_REPLACE, rest_tracks)
                await command_bus.execute(CMD_PLAY_TRACK, first_track)

    elif action == "enqueue_genre_songs":
        genre_name = data.get("genre")
        if genre_name:
            await db.increment_genre_click(genre_name)
            songs = await db.get_genre_songs(genre_name, total_limit=12, max_per_artist=3)
            if songs:
                await command_bus.execute(CMD_SET_MODE, PlaybackMode.QUEUE)
                await command_bus.execute(CMD_QUEUE_REPLACE, songs)
                await command_bus.execute(CMD_QUEUE_SELECT, 0)

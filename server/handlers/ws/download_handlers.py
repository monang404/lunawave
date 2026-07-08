import os

import structlog

from core.commands import DownloadCommand
from core.state import TrackInfo
from core.utils import user_download_path
from core.ws_actions import WSAction
from server.handlers.ws.registry import register_ws_handler

logger = structlog.get_logger(__name__)

@register_ws_handler(WSAction.DOWNLOAD)
async def _handle_download(data, ws, state, ytdlp, manager, db, command_bus):
    track = TrackInfo.from_dict(data) if data else None
    await command_bus.execute(DownloadCommand(track=track))  # type: ignore

@register_ws_handler(WSAction.DELETE_DOWNLOAD)
async def _handle_delete_download(data, ws, state, ytdlp, manager, db, command_bus):
    track = TrackInfo.from_dict(data) if data else None
    if track and track.video_id:
        db_track = await db.get_track(track.video_id)
        if db_track and db_track.local_path:
            if os.path.exists(db_track.local_path):
                try:
                    os.remove(db_track.local_path)
                except Exception as e:
                    logger.error(f"Gagal menghapus cache {db_track.local_path}: {e}")

            user_path = user_download_path(db_track.artist, db_track.title)
            if user_path.exists():
                try:
                    os.remove(str(user_path))
                except OSError as e:
                    logger.error(f"Gagal hapus file user download {user_path}: {e}")

            db_track.local_path = None
            await db.set_local_path(db_track.video_id, None)

            if state.current_track and state.current_track.video_id == db_track.video_id:
                state.current_track.local_path = None
                await manager.broadcast({
                    "type": "state",
                    "data": state.to_dict()
                })

            await manager.broadcast({
                "type": "log",
                "data": f"Unduhan dihapus: {db_track.title}"
            })


import time

import structlog

from core.events import (
    DownloadCompleteEvent,
    DownloadProgressEvent,
    LogMessageEvent,
    LyricsUpdatedEvent,
    QueueUpdatedEvent,
    TrackPauseChangedEvent,
    TrackProgressEvent,
    TrackStartedEvent,
)
from core.task_utils import safe_create_task
from server.services.broadcast_service import BroadcastService
from server.services.stream_prefetch import StreamPrefetchService

logger = structlog.get_logger(__name__)

def setup_event_listeners(
    playback_controller,
    prefetch_service: StreamPrefetchService,
    broadcast_service: BroadcastService
):
    async def _on_track_started(event: TrackStartedEvent):
        state = playback_controller.state
        _next = None
        if state.queue:
            _next = state.queue[0]
        elif state.radio_queue:
            _next = state.radio_queue[0]
        if _next and _next.video_id:
            safe_create_task(prefetch_service.prefetch_stream_url(_next.video_id), name=f"prefetch_next_{_next.video_id}")

        await broadcast_service.broadcast_state(state)

    _last_progress_time = 0.0

    async def _on_track_progress(event: TrackProgressEvent):
        nonlocal _last_progress_time
        now = time.monotonic()
        if now - _last_progress_time < 0.5:
            return
        _last_progress_time = now
        position = event.position
        await broadcast_service.broadcast_progress(position, playback_controller.state.status.name)

    async def _on_queue_updated(event: QueueUpdatedEvent):
        await broadcast_service.broadcast_state(playback_controller.state)

    async def _on_lyrics_updated(event: LyricsUpdatedEvent):
        await broadcast_service.broadcast_lyrics(playback_controller.state)

    async def _on_download_complete(event: DownloadCompleteEvent):
        await broadcast_service.broadcast_state(playback_controller.state)
        if event.track:
            await playback_controller.resolver.db.upsert_track(event.track, local_path=event.track.local_path)

        db = playback_controller.resolver.db
        recent = await db.get_recent_tracks(20)
        favorites = await db.get_favorite_tracks()
        cached_tracks = await db.get_cached_tracks(50)
        data = {
            "type": "discover_data",
            "data": {
                "recent": [t.to_dict() for t in recent],
                "favorites": [t.to_dict() for t in favorites],
                "cached_tracks": [t.to_dict() for t in cached_tracks],
            }
        }
        await broadcast_service.manager.broadcast(data)

    async def _on_log_message(event: LogMessageEvent):
        msg = event.message
        playback_controller.state.error_msg = msg
        await broadcast_service.broadcast_log(msg)

    async def _on_pause_changed(event: TrackPauseChangedEvent):
        await broadcast_service.broadcast_progress(playback_controller.state.position, playback_controller.state.status.name)

    async def _on_download_progress(event: DownloadProgressEvent):
        await broadcast_service.broadcast_download_progress(event.progress)

    bus = playback_controller.bus
    bus.subscribe(TrackStartedEvent, _on_track_started)
    bus.subscribe(TrackProgressEvent, _on_track_progress)
    bus.subscribe(QueueUpdatedEvent, _on_queue_updated)
    bus.subscribe(LyricsUpdatedEvent, _on_lyrics_updated)
    bus.subscribe(DownloadCompleteEvent, _on_download_complete)
    bus.subscribe(LogMessageEvent, _on_log_message)
    bus.subscribe(TrackPauseChangedEvent, _on_pause_changed)
    bus.subscribe(DownloadProgressEvent, _on_download_progress)
    logger.info("EventBus subscriptions set up for Web Server")

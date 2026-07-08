import structlog

from core.events import LogMessageEvent, QueueUpdatedEvent

logger = structlog.get_logger(__name__)

class QueueCommands:
    def __init__(self, playback_controller):
        self.playback_controller = playback_controller
        self.state = playback_controller.state
        self.bus = playback_controller.bus

    async def on_queue_select(self, cmd):
        async with self.playback_controller._lock:
            if 0 <= cmd.index < len(self.state.queue):
                track = self.state.queue[cmd.index]
                for _ in range(cmd.index + 1):
                    self.state.queue.popleft()
                await self.playback_controller.play_track(track)

    async def on_queue_remove(self, cmd):
        async with self.playback_controller._lock:
            if 0 <= cmd.index < len(self.state.queue):
                removed = self.state.queue[cmd.index]
                del self.state.queue[cmd.index]
                await self.bus.publish(QueueUpdatedEvent())
                await self.bus.publish(LogMessageEvent(message=f"Dihapus dari antrean: {removed.title}"))

    async def on_queue_add(self, cmd):
        async with self.playback_controller._lock:
            self.state.queue.append(cmd.track)
            await self.bus.publish(QueueUpdatedEvent())
            await self.bus.publish(LogMessageEvent(message=f"Ditambahkan ke antrean: {cmd.track.title}"))

    async def on_queue_replace(self, cmd):
        async with self.playback_controller._lock:
            self.state.queue.clear()
            self.state.queue.extend(cmd.tracks)
            await self.bus.publish(QueueUpdatedEvent())

    async def on_queue_reorder(self, cmd):
        async with self.playback_controller._lock:
            q = self.state.queue
            if 0 <= cmd.from_index < len(q) and 0 <= cmd.to_index < len(q):
                item = q[cmd.from_index]
                del q[cmd.from_index]
                q.insert(cmd.to_index, item)
                await self.bus.publish(QueueUpdatedEvent())

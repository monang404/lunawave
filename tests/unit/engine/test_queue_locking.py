"""
PATCH-1-04: Fix _on_queue_remove tidak punya lock (HIDDEN-05)
Verifikasi bahwa _on_queue_remove menggunakan self._lock.
"""

import inspect

from engine.playback.queue_commands import QueueCommands
from engine.playback.playback_commands import PlaybackCommands


class TestQueueRemoveLock:
    """Checklist PATCH-1-04:
    - [x] Kode on_queue_remove menggunakan 'async with self.playback_controller._lock:'
    """

    def test_on_queue_remove_uses_lock(self):
        """on_queue_remove HARUS menggunakan 'async with self.playback_controller._lock'."""
        source = inspect.getsource(QueueCommands.on_queue_remove)
        assert "async with self.playback_controller._lock" in source, (
            "on_queue_remove HARUS menggunakan 'async with self.playback_controller._lock:' "
            "untuk mencegah race condition dengan on_queue_select"
        )

    def test_on_queue_select_uses_lock(self):
        """on_queue_select juga HARUS menggunakan self.playback_controller._lock (sanity check)."""
        source = inspect.getsource(QueueCommands.on_queue_select)
        assert "async with self.playback_controller._lock" in source, (
            "on_queue_select harus menggunakan 'async with self.playback_controller._lock:'"
        )

    def test_on_next_uses_lock(self):
        """on_next juga HARUS menggunakan self.playback_controller._lock (sanity check)."""
        source = inspect.getsource(PlaybackCommands.on_next)
        assert "async with self.playback_controller._lock" in source, (
            "on_next harus menggunakan 'async with self.playback_controller._lock:'"
        )

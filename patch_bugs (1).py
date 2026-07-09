#!/usr/bin/env python3
"""
LunaWave Bug Patch Script — v2
Jalankan dari root direktori project: python patch_bugs.py
"""
import sys
from pathlib import Path

BASE = Path(__file__).parent
errors = []
applied = []

def patch(rel_path, old, new, desc):
    path = BASE / rel_path
    if not path.exists():
        errors.append(f"FILE NOT FOUND: {rel_path}")
        return
    content = path.read_text(encoding="utf-8")
    if old not in content:
        if new.split("\n")[0] in content or new in content:
            print(f"  [SKIP] {desc}")
        else:
            errors.append(f"PATTERN NOT FOUND in {rel_path}: {repr(old[:80])}")
        return
    path.write_text(content.replace(old, new, 1), encoding="utf-8")
    applied.append(desc)
    print(f"  [OK]   {desc}")

print("=== LunaWave Bug Patch v2 ===\n")

# ─── PATCH 1 (KRITIS) ────────────────────────────────────────────────────────
# time.monotonic() → time.time() di auth.py
# Root cause: token selalu expired → refresh = logout → WS putus → lagu hilang
patch(
    "server/handlers/auth.py",
    "        now = time.monotonic()\n",
    "        now = time.time()\n",
    "PATCH 1: auth.py — time.monotonic() → time.time()"
)

# ─── PATCH 2 ─────────────────────────────────────────────────────────────────
# stop_status_bar() tidak pernah dibuat setelah refactor
patch(
    "core/cli_ui.py",
    "def start_ui_threads():",
    'def stop_status_bar():\n    """Hentikan status bar worker — dipanggil saat shutdown atau dari test."""\n    global _status_bar_active\n    _status_bar_active = False\n    _stop_event.set()\n\ndef start_ui_threads():',
    "PATCH 2: cli_ui.py — tambah stop_status_bar()"
)

# ─── PATCH 3 ─────────────────────────────────────────────────────────────────
# Test import salah modul (sudah pindah ke core.cli_ui setelah refactor)
patch(
    "tests/unit/core/test_log_config.py",
    "    from core.log_config import _status_bar_worker, _stop_event, stop_status_bar",
    "    from core.cli_ui import _status_bar_worker, _stop_event, stop_status_bar",
    "PATCH 3a: test_log_config.py — fix import _status_bar_worker"
)
patch(
    "tests/unit/core/test_log_config.py",
    "    from core.log_config import _stop_event, _summary_worker",
    "    from core.cli_ui import _stop_event, _summary_worker",
    "PATCH 3b: test_log_config.py — fix import _summary_worker"
)
patch(
    "tests/unit/core/test_log_config.py",
    "    import core.log_config\n    core.log_config._status_bar_active = True",
    "    import core.cli_ui\n    core.cli_ui._status_bar_active = True",
    "PATCH 3c: test_log_config.py — fix module ref _status_bar_active"
)

# ─── PATCH 4 ─────────────────────────────────────────────────────────────────
# DownloadManager.shutdown() — 3 worker task tidak pernah di-cancel saat exit
patch(
    "engine/download_manager.py",
    "    def _route(self, action):",
    '    async def shutdown(self):\n        """Cancel semua download worker saat aplikasi shutdown."""\n        for t in self._workers:\n            if not t.done():\n                t.cancel()\n        self._workers.clear()\n\n    def _route(self, action):',
    "PATCH 4: download_manager.py — tambah shutdown()"
)

# ─── PATCH 5 ─────────────────────────────────────────────────────────────────
# bootstrap.py — expose download_manager ke AppContext
patch(
    "core/bootstrap.py",
    "    host: str\n    port: int",
    "    download_manager: Any\n    host: str\n    port: int",
    "PATCH 5a: bootstrap.py — tambah download_manager ke AppContext"
)
patch(
    "core/bootstrap.py",
    "    _download_manager = DownloadManager(event_bus, command_bus, state, ytdlp)",
    "    download_manager = DownloadManager(event_bus, command_bus, state, ytdlp)",
    "PATCH 5b: bootstrap.py — _download_manager → download_manager"
)
patch(
    "core/bootstrap.py",
    "        sponsorblock=sponsorblock,\n        host=host,",
    "        sponsorblock=sponsorblock,\n        download_manager=download_manager,\n        host=host,",
    "PATCH 5c: bootstrap.py — sertakan download_manager di AppContext return"
)
patch(
    "core/bootstrap.py",
    "    # Cancel download workers\n    # Cancel persist_state_task",
    "    # Cancel download workers\n    try:\n        await ctx.download_manager.shutdown()\n    except Exception:\n        pass\n    # Cancel persist_state_task",
    "PATCH 5d: bootstrap.py — cancel download workers saat shutdown"
)

# ─── PATCH 6 ─────────────────────────────────────────────────────────────────
# event_listeners.py — discover_data payload pasca-download tidak punya featured_artists/genres
patch(
    "server/handlers/event_listeners.py",
    "from core.task_utils import safe_create_task\n"
    "from server.services.broadcast_service import BroadcastService",
    "from core.task_utils import safe_create_task\n"
    "from server.handlers.ws.discover_handlers import _build_discover_payload\n"
    "from server.services.broadcast_service import BroadcastService",
    "PATCH 6a: event_listeners.py — import _build_discover_payload"
)
patch(
    "server/handlers/event_listeners.py",
    "        db = playback_controller.resolver.db\n"
    "        recent = await db.get_recent_tracks(20)\n"
    "        favorites = await db.get_favorite_tracks()\n"
    "        cached_tracks = await db.get_cached_tracks(50)\n"
    "        data = {\n"
    "            \"type\": \"discover_data\",\n"
    "            \"data\": {\n"
    "                \"recent\": [t.to_dict() for t in recent],\n"
    "                \"favorites\": [t.to_dict() for t in favorites],\n"
    "                \"cached_tracks\": [t.to_dict() for t in cached_tracks],\n"
    "            }\n"
    "        }\n"
    "        await broadcast_service.manager.broadcast(data)",
    "        db = playback_controller.resolver.db\n"
    "        data = await _build_discover_payload(db)\n"
    "        await broadcast_service.manager.broadcast(data)",
    "PATCH 6b: event_listeners.py — pakai _build_discover_payload (schema konsisten)"
)

# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*44}")
print(f"Applied : {len(applied)}")
print(f"Errors  : {len(errors)}")
if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("\nSemua patch berhasil. Jalankan: python main.py")

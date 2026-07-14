import os
import shutil

# 1. Delete duplicates
files_to_delete = [
    "tests/unit/engine/test_playback_queue_ops.py",
    "tests/unit/engine/test_playback_mode_ops.py",
]
for f in files_to_delete:
    if os.path.exists(f):
        os.remove(f)
        print(f"Deleted {f}")

# 2. Move test_track_loader.py
src = "tests/unit/engine/test_track_loader.py"
dst = "tests/unit/engine/playback/test_track_loader.py"
if os.path.exists(src):
    shutil.move(src, dst)
    print(f"Moved {src} to {dst}")

# 3. Create missing test files
missing_files = [
    "tests/unit/engine/radio/test_track_filter.py",
    "tests/unit/server/handlers/test_event_listeners.py",
    "tests/unit/server/handlers/test_websocket.py",
    "tests/unit/server/handlers/test_ws_playback.py",
    "tests/unit/server/handlers/test_ws_queue.py",
    "tests/unit/server/handlers/test_ws_discovery.py",
    "tests/unit/server/handlers/test_ws_download.py",
    "tests/unit/server/services/test_broadcast_service.py",
    "tests/unit/server/services/test_stream_prefetch.py",
    "tests/unit/plugins/test_lyrics_fetcher.py",
    "tests/unit/plugins/test_notifications.py",
    "tests/unit/plugins/test_sponsorblock.py",
    "tests/unit/launcher/test_process.py",
    "tests/unit/launcher/test_network.py",
    "tests/unit/launcher/test_updater.py",
    "tests/unit/launcher/gui/test_status_panel.py",
    "tests/unit/launcher/gui/test_log_panel.py",
    "tests/unit/scripts/test_export_to_sqlite.py",
]

template = '''"""
Module: {module_path}

Purpose:
    Auto-generated test scaffold.

Subscribes to:
    None

Publishes:
    None
"""

import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_placeholder():
    pass
'''

for mf in missing_files:
    os.makedirs(os.path.dirname(mf), exist_ok=True)
    if not os.path.exists(mf):
        module_path = mf.replace("/", ".").replace("\\", ".").replace(".py", "")
        with open(mf, "w", encoding="utf-8") as f:
            f.write(template.format(module_path=module_path))
        print(f"Created {mf}")

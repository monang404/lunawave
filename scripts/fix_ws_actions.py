import os
import re

js_dir = os.path.join(os.path.dirname(__file__), '..', 'web', 'static', 'js')

actions = [
    "play_track", "toggle_pause", "next", "prev", "stop", "seek",
    "queue_select", "queue_remove", "queue_add", "queue_reorder", "enqueue_artist_songs", "enqueue_genre_songs",
    "radio_randomize",
    "volume_up", "volume_down", "volume_set", "set_mode", "set_output", "set_sponsorblock", "lyrics_offset",
    "download", "delete_download",
    "search", "discover", "toggle_favorite", "auth"
]

for root, _, files in os.walk(js_dir):
    for file in files:
        if file.endswith('.js'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for action in actions:
                # Replace wsSend("action", ...) or wsSend('action', ...)
                pattern = r"wsSend\s*\(\s*['\"]" + action + r"['\"]"
                replacement = "wsSend(WS_ACTIONS." + action.upper() + ""
                content = re.sub(pattern, replacement, content)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

print("Updated all wsSend calls.")

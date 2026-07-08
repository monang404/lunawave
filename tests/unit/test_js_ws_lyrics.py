import pytest
import os
from config import BASE_DIR

def test_ws_js_has_lyrics_raf_debounce():
    """Verify that ws.js properly debounces the requestAnimationFrame for syncLocalLyrics."""
    js_path = BASE_DIR / "web" / "static" / "js" / "ws.js"
    assert js_path.exists(), "ws.js not found"
    
    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "window._syncLyricsRaf" in content, "Missing _syncLyricsRaf state variable"
    assert "window._syncLyricsRaf = null" in content, "Missing resetting of _syncLyricsRaf inside raf callback"

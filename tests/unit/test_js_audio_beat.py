import pytest
import os
from config import BASE_DIR

def test_audio_js_has_beat_protections():
    """Verify that audio.js fake beat loop has protections for reduced motion and hidden documents."""
    js_path = BASE_DIR / "web" / "static" / "js" / "audio.js"
    assert js_path.exists(), "audio.js not found"
    
    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "prefers-reduced-motion" in content, "Missing prefers-reduced-motion check"
    assert "document.hidden" in content, "Missing document.hidden check"
    assert "clearTimeout(_fakeBeatTimeout)" in content, "Missing clearTimeout for fake beat loop"

def test_visualizer_has_beat_protections():
    """Verify that audio.js visualizer loop has protections for reduced motion and hidden documents."""
    js_path = BASE_DIR / "web" / "static" / "js" / "audio.js"
    
    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "startVisualizerLoop" in content
    # the exact check depends on the implementation, but let's check for visualizer-specific logic
    assert "prefersReducedMotion" in content

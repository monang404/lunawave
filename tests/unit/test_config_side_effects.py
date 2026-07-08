import sys
import os
import shutil
import importlib
from pathlib import Path

def test_config_has_no_side_effects(monkeypatch, tmp_path):
    # This test verifies that importing config.py does NOT perform I/O side effects like creating directories
    
    # We monkeypatch the LUNAWAVE_BASE to a temporary directory so we don't pollute real cache
    base_dir = tmp_path / "test_base"
    monkeypatch.setenv("LUNAWAVE_BASE", str(base_dir))
    
    # Force reload of config module
    if 'config' in sys.modules:
        importlib.reload(sys.modules['config'])
    else:
        import config
    
    # Verify that 'cache/sockets' was NOT created by the import!
    sockets_dir = base_dir / "cache" / "sockets"
    assert not sockets_dir.exists(), "config.py should not create directories on import!"

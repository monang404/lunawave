"""
Module: launcher.gui.dep_checker

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import importlib.util
import shutil

class DependencyChecker:
    def check_dependencies(self) -> tuple[list[str], bool]:
        deps = {
            "yt-dlp": "yt_dlp",
            "aiosqlite": "aiosqlite",
            "aiohttp": "aiohttp",
            "syncedlyrics": "syncedlyrics",
            "structlog": "structlog",
            "prometheus_client": "prometheus_client",
            "opentelemetry": "opentelemetry"
        }
        missing = []
        for label, import_name in deps.items():
            try:
                spec = importlib.util.find_spec(import_name)
                if spec is None:
                    missing.append(label)
            except Exception:
                missing.append(label)

        mpv_ok = shutil.which("mpv") is not None
        return missing, mpv_ok

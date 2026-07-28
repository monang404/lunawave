"""
Module: launcher.dep_checker

Purpose:
    Utility to verify required system dependencies before launching the application.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread.
"""

import importlib.util
import shutil
import socket
import subprocess

import structlog

# PATCH-2026-07-28 (temuan #9, P4-T1c): launcher/ adalah entry-point, bukan
# infrastruktur logging itu sendiri (beda dengan core/log_context.py) --
# tidak ada risiko circular-import menambah logger structlog di sini.
# Konvensi mengikuti launcher/preflight.py (satu-satunya file launcher/
# yang sudah pakai logging sebelum perubahan ini).
logger = structlog.get_logger(component="launcher.dep_checker")


class DependencyChecker:
    def check_dependencies(self) -> tuple[list[str], bool]:
        deps = {
            "yt-dlp": "yt_dlp",
            "aiosqlite": "aiosqlite",
            "aiohttp": "aiohttp",
            "syncedlyrics": "syncedlyrics",
            "structlog": "structlog",
            "prometheus_client": "prometheus_client",
            "opentelemetry": "opentelemetry",
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

    def check_port(self, host: str, port: int) -> bool:
        """
        Returns True if the port is currently IN USE (occupied), False otherwise.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex((host, int(port))) == 0
        except Exception:
            return False

    def mpv_version(self) -> str | None:
        """
        Returns the first line of mpv --version output, or None if fail/not found.
        """
        # Klasifikasi: best-effort cleanup. Deteksi versi mpv gagal (mis.
        # timeout, biner rusak) tidak boleh menggagalkan preflight check --
        # hanya berarti versi tidak ditampilkan. Debug-level untuk membantu
        # diagnosis kalau ada laporan "MPV terdeteksi tapi versi kosong".
        try:
            if shutil.which("mpv") is None:
                return None
            res = subprocess.run(["mpv", "--version"], capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0 and res.stdout:
                return res.stdout.splitlines()[0].strip()
        except Exception as e:
            logger.debug("mpv_version_check_failed", error=str(e))
        return None

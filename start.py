#!/usr/bin/env python3
"""
bagas.fm — Server Manager
Jalankan: python start.py
"""

try:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext
except ImportError:
    import sys
    print("Tkinter is not available. Please run `main.py` directly or use `start.sh` on headless environments like Termux.", file=sys.stderr)
    sys.exit(1)
import importlib.util
import os
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

BASE_DIR   = Path(__file__).parent
SERVER_PORT = int(os.environ.get("LunaWave_PORT", 8765))
PYTHON     = sys.executable

BG         = "#0E0E12"
BG_SURFACE = "#151518"
BG_CARD    = "#1C1C22"
ACCENT     = "#F2B544"
TEXT_1     = "#FFFFFF"
TEXT_2     = "#9AA0AA"
TEXT_3     = "#60656F"
GREEN      = "#22C55E"
RED        = "#EF4444"
BORDER     = "#2A2A32"

class DependencyChecker:
    @staticmethod
    def check_dependencies():
        deps = {
            "yt-dlp": "yt_dlp",
            "aiosqlite": "aiosqlite",
            "aiohttp": "aiohttp",
            "syncedlyrics": "syncedlyrics",
            "structlog": "structlog",
            "prometheus_client": "prometheus_client"
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


class ServerProcessManager:
    def __init__(self, base_dir, python_exec):
        self.process = None
        self.base_dir = base_dir
        self.python_exec = python_exec

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def check_port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0

    def get_pid_occupying_port(self, port: int) -> int | None:
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(['netstat', '-aon'], text=True)
                for line in output.splitlines():
                    if "TCP" in line.upper():
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            local_addr = parts[1]
                            pid = parts[-1]
                            if (local_addr.endswith(f":{port}") or local_addr.endswith(f"]:{port}")) and pid.isdigit() and pid != "0":
                                return int(pid)
            except Exception:
                pass
        else:
            try:
                output = subprocess.check_output(['lsof', '-t', f'-i:{port}'], text=True)
                pids = output.strip().split()
                if pids:
                    return int(pids[0])
            except Exception:
                try:
                    output = subprocess.check_output(['fuser', f'{port}/tcp'], text=True)
                    parts = output.strip().split()
                    if parts:
                        return int(parts[-1])
                except Exception:
                    try:
                        output = subprocess.check_output(['ss', '-lptn', f'sport = :{port}'], text=True)
                        import re
                        m = re.search(r'pid=(\d+)', output)
                        if m:
                            return int(m.group(1))
                    except Exception:
                        pass
        return None

    def kill_process_tree(self, pid: int):
        if sys.platform == "win32":
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:
            try:
                import signal
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except Exception:
                try:
                    import signal
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass

    def start(self, port, env, on_log_cb=None):
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs["preexec_fn"] = os.setsid

        self.process = subprocess.Popen(
            [self.python_exec, "main.py"],
            cwd=str(self.base_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
            errors="replace",
            encoding="utf-8",
            **kwargs
        )

        if on_log_cb:
            def _pipe():
                try:
                    for line in self.process.stdout:
                        line = line.rstrip()
                        if not line:
                            continue
                        tag = "err" if any(w in line.lower() for w in ("error", "exception", "traceback", "critical")) else "ok" if any(w in line.lower() for w in ("started", "ready", "listening", "running")) else ""
                        on_log_cb(line, tag)
                except Exception:
                    pass
                on_log_cb("── process ended ──", "dim")
            threading.Thread(target=_pipe, daemon=True).start()

    def wait_stop(self):
        try:
            self.process.wait(timeout=6)
        except subprocess.TimeoutExpired:
            try:
                self.process.kill()
            except Exception:
                pass



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--headless":
        print("Running in headless mode...")
        manager = ServerProcessManager(BASE_DIR, PYTHON)
        port = int(os.environ.get("LunaWave_PORT", 8765))
        manager.start(port)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop()
    else:
        try:
            from gui_manager import ServerManagerWindow
            app = ServerManagerWindow()
            app.mainloop()
        except ImportError as e:
            print(f"Failed to start GUI: {e}")
            print("Running in headless mode as fallback...")
            manager = ServerProcessManager(BASE_DIR, PYTHON)
            port = int(os.environ.get("LunaWave_PORT", 8765))
            manager.start(port)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop()

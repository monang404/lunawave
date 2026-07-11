"""
Module: launcher.process

Purpose:
    Manage OS-level lifecycle for the LunaWave server and mpv processes
    from the desktop launcher.

Responsibilities:
    - Kill process trees cross-platform (SIGKILL / taskkill).
    - Start main.py as a subprocess and pipe its stdout to the GUI log.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (stdout piped in a daemon thread; Popen is thread-safe).
"""

import subprocess
import os
import sys
import threading
import time

def kill_process_tree(pid: int):
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

def kill_mpv():
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "mpv.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
        try:
            subprocess.run(["pkill", "-f", "mpv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

class ServerProcess:
    def __init__(self, cwd: str, port: int, on_log=None):
        self.cwd = cwd
        self.port = port
        self.process = None
        self.on_log = on_log

    def start(self) -> subprocess.Popen:
        env = os.environ.copy()
        env["LUNAWAVE_HOST"] = "0.0.0.0"
        env["LUNAWAVE_PORT"] = str(self.port)
        env["YTGUI_HOST"] = "0.0.0.0"
        env["YTGUI_PORT"] = str(self.port)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs["preexec_fn"] = os.setsid
            
        python_exe = sys.executable
        self.process = subprocess.Popen(
            [python_exe, "main.py"],
            cwd=self.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
            errors="replace",
            encoding="utf-8",
            **kwargs
        )
        
        if self.on_log:
            threading.Thread(target=self._pipe_stdout, daemon=True).start()
            
        return self.process

    def _pipe_stdout(self):
        try:
            for line in self.process.stdout:
                line = line.rstrip()
                if not line:
                    continue
                if self.on_log:
                    self.on_log(line)
        except Exception:
            pass
        if self.on_log:
            self.on_log("── process ended ──", is_end=True)

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self, wait_timeout=6):
        if not self.is_running():
            return
        kill_process_tree(self.process.pid)
        try:
            self.process.wait(timeout=wait_timeout)
        except subprocess.TimeoutExpired:
            try:
                self.process.kill()
            except Exception:
                pass

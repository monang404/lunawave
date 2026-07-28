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

import os
import subprocess
import sys
import threading

import structlog

# PATCH-2026-07-28 (temuan #9, P4-T1c): launcher/ adalah entry-point, tidak
# ada risiko circular-import. Konvensi mengikuti launcher/preflight.py.
logger = structlog.get_logger(component="launcher.process")


def kill_process_tree(pid: int):
    if sys.platform == "win32":
        # Klasifikasi: best-effort cleanup. taskkill gagal (mis. proses
        # sudah exit duluan) tidak boleh menggagalkan shutdown launcher.
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.debug("kill_process_tree_failed", platform="win32", pid=pid, error=str(e))
    else:
        try:
            import signal

            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except Exception:
            # Klasifikasi: best-effort cleanup. Fallback dari killpg (mis.
            # proses bukan group leader) ke kill langsung -- kalau
            # keduanya gagal, proses kemungkinan sudah mati duluan.
            try:
                import signal

                os.kill(pid, signal.SIGKILL)
            except Exception as e:
                logger.debug("kill_process_tree_failed", platform="unix", pid=pid, error=str(e))


def kill_mpv():
    if sys.platform == "win32":
        # Klasifikasi: best-effort cleanup. Taskkill mpv.exe gagal (mis.
        # tidak ada instance mpv jalan) tidak boleh menggagalkan shutdown.
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "mpv.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.debug("kill_mpv_failed", platform="win32", error=str(e))
    else:
        try:
            subprocess.run(
                ["pkill", "-f", "mpv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.debug("kill_mpv_failed", platform="unix", error=str(e))


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
        self.process = subprocess.Popen(  # type: ignore
            [python_exe, "main.py"],
            cwd=self.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            errors="replace",
            encoding="utf-8",
            **kwargs,
        )

        if self.on_log:
            threading.Thread(target=self._pipe_stdout, daemon=True).start()

        return self.process  # type: ignore

    def _pipe_stdout(self):
        # Klasifikasi: best-effort cleanup. Pipe stdout putus adalah kejadian
        # normal saat proses server di-kill (mis. dari stop()) -- tidak
        # boleh melempar di thread daemon ini. Debug-level juga membantu
        # kalau penyebabnya bug di callback on_log, bukan cuma pipe closed.
        try:
            for line in self.process.stdout:
                line = line.rstrip()
                if not line:
                    continue
                if self.on_log:
                    self.on_log(line)
        except Exception as e:
            logger.debug("pipe_stdout_failed", error=str(e))
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
            # Klasifikasi: best-effort cleanup. Proses menolak/gagal mati
            # walau sudah dikirim SIGKILL/taskkill -- kemungkinan besar
            # sudah exit tepat di antara kill_process_tree() dan kill() ini
            # (race benign). Debug-level untuk membantu diagnosis kalau
            # ternyata proses benar-benar nyangkut (zombie/defunct).
            try:
                self.process.kill()
            except Exception as e:
                logger.debug("force_kill_failed", pid=self.process.pid, error=str(e))

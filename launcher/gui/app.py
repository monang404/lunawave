"""
Module: launcher.gui

Purpose:
    Provide the Tkinter-based ServerManager GUI for starting, stopping,
    and monitoring the LunaWave backend server.

Responsibilities:
    - Render server status, port picker, quick links, and dependency checks.
    - Manage server process lifecycle and stream stdout to the log panel.

Depends on:
    - launcher
    - launcher.gui.auth_panel
    - launcher.gui.controller
    - launcher.gui.dep_checker
    - launcher.gui.ui_builder

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread only (all Tkinter calls must stay on the main thread).
"""

import os
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

from launcher import network

# ── Config ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SERVER_PORT = int(os.environ.get("LUNAWAVE_PORT", os.environ.get("YTGUI_PORT", 8765)))
PYTHON = sys.executable

# ── Colors (LunaWave dark theme) ─────────────────────────
BG = "#0E0E12"
BG_SURFACE = "#151518"
BG_CARD = "#1C1C22"
ACCENT = "#F2B544"
TEXT_1 = "#FFFFFF"
TEXT_2 = "#9AA0AA"
TEXT_3 = "#60656F"
GREEN = "#22C55E"
RED = "#EF4444"
BORDER = "#2A2A32"


class ServerManager(tk.Tk):
    def __init__(self):
        super().__init__()

        self.server_process = None
        self._log_lock = threading.Lock()
        self._conflict_pid = None
        self._last_stdout_line = ""
        self._closing = False

        self._btn_start = None
        self._btn_stop = None
        self._btn_restart = None
        self._btn_open = None
        self._port_entry = None
        self._btn_kill_conflict = None
        self._pid_label = None
        self._dot = None
        self._status_label = None
        self._log = None
        self._deps_status = None

        self._port_var = tk.StringVar(value=str(SERVER_PORT))
        from launcher.gui.controller import ServerController

        self.controller = ServerController(self, BASE_DIR)

        self._build_window()
        self._build_ui()
        self._run_dependency_check()
        self._refresh_status()
        from launcher.gui.auth_panel import handle_first_run

        handle_first_run(
            self,
            BASE_DIR,
            BG,
            BG_CARD,
            BG_SURFACE,
            ACCENT,
            TEXT_1,
            TEXT_2,
            TEXT_3,
            RED,
            GREEN,
            BORDER,
        )

    # ── Window setup ──────────────────────────────────────
    def _build_window(self):
        self.title("LunaWave — Server Manager")
        self.geometry("600x680")
        self.minsize(520, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"+{x}+{y}")

        try:
            icon_path = BASE_DIR / "web" / "static" / "icons" / "icon-512.png"
            if icon_path.exists():
                img = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, img)
            else:
                self.iconbitmap(default="")
        except Exception:
            pass

    # ── UI Layout ──
    def _build_ui(self):
        from launcher.gui.ui_builder import UIBuilder

        builder = UIBuilder(
            BG, BG_SURFACE, BG_CARD, ACCENT, TEXT_1, TEXT_2, TEXT_3, GREEN, RED, BORDER, BASE_DIR
        )
        builder.build_ui(self)

    @property
    def server_port(self) -> int:
        try:
            return int(self._port_var.get().strip())
        except ValueError:
            return 8765

    # ── Safe scheduling ────────────────────────────────────
    def _safe_after(self, delay, callback):
        """Schedule `callback` via Tk's `after`, unless the window is
        already closing/destroyed.

        Background threads (dependency check, server-ready poller, stdout
        pipe, restart timer) all eventually call back into the GUI via
        `after()`. Without this guard, a thread that finishes after the
        user has closed the window raises an unhandled RuntimeError/
        TclError ("main thread is not in main loop" / "invalid command
        name ...") in that thread — confirmed via reproduction
        (PATCH-2026-07-16-002). This does not crash the process (daemon
        threads), but it is an unguarded exit path that pollutes logs and
        can mask real errors.
        """
        if self._closing:
            return
        try:
            self.after(delay, callback)
        except (RuntimeError, tk.TclError):
            pass

    # ── Dependency Checker ─────────────────────────────────
    def _run_dependency_check(self):
        def _thread_fn():
            from launcher.gui.dep_checker import DependencyChecker

            checker = DependencyChecker()
            missing, mpv_ok = checker.check_dependencies()
            if not missing and mpv_ok:
                status_text = "✓ Python Libraries: OK  ·  ✓ MPV Audio Player: OK"
                color = GREEN
            else:
                parts = []
                if missing:
                    parts.append(f"✗ Missing libraries: {', '.join(missing)}")
                else:
                    parts.append("✓ Python Libraries: OK")
                if not mpv_ok:
                    parts.append("✗ MPV Player missing from PATH")
                else:
                    parts.append("✓ MPV Player: OK")
                status_text = "  ·  ".join(parts)
                color = RED

            self._safe_after(0, lambda: self._deps_status.config(text=status_text, fg=color))

        threading.Thread(target=_thread_fn, daemon=True).start()

    # ── Status ────────────────────────────────────────────
    def _is_running(self) -> bool:
        return self.server_process is not None and self.server_process.is_running()

    def _refresh_status(self):
        if self._closing:
            return
        port = self.server_port
        running = self._is_running()

        if running:
            status = "RUNNING"
            color = GREEN
            self._pid_label.config(text=f"PID {self.server_process.process.pid}  ·  :{port}")
            self._btn_start.config(state="disabled")
            self._btn_stop.config(state="normal")
            self._btn_restart.config(state="normal")
            self._btn_open.config(state="normal")
            self._port_entry.config(state="disabled")
            self._btn_kill_conflict.pack_forget()
        else:
            in_use = False
            conflict_pid = None
            if network.check_port_in_use(port):
                in_use = True
                conflict_pid = network.get_pid_occupying_port(port)

            if in_use:
                status = "CONFLICT"
                color = ACCENT
                pid_text = f"PID {conflict_pid}" if conflict_pid else "Unknown PID"
                self._pid_label.config(text=f"Port :{port} used by {pid_text}")
                self._btn_start.config(state="disabled")
                self._btn_stop.config(state="disabled")
                self._btn_restart.config(state="disabled")
                self._btn_open.config(state="normal")
                self._port_entry.config(state="normal")

                self._conflict_pid = conflict_pid
                self._btn_kill_conflict.config(
                    text=f"☠  Kill Process (PID {conflict_pid})"
                    if conflict_pid
                    else "☠  Kill Port Owner"
                )
                self._btn_kill_conflict.pack(side="right", padx=(5, 0))
            else:
                status = "STOPPED"
                color = RED
                self._pid_label.config(text=f"Port :{port}")
                self._btn_start.config(state="normal")
                self._btn_stop.config(state="disabled")
                self._btn_restart.config(state="disabled")
                self._btn_open.config(state="disabled")
                self._port_entry.config(state="normal")
                self._btn_kill_conflict.pack_forget()

        # Update Dot
        self._dot.delete("all")
        self._dot.create_oval(1, 1, 9, 9, fill=color, outline="")

        # Update status label text
        self._status_label.config(text=status, fg=color)

        self._safe_after(2000, self._refresh_status)

    # ── Log helpers ───────────────────────────────────────
    def _write_log(self, msg: str, tag: str = "", is_end: bool = False):
        def _do():
            self._log.config(state="normal")
            if is_end:
                self._log.insert("end", msg.rstrip() + "\n", "dim")
            else:
                ts = time.strftime("%H:%M:%S")
                self._log.insert("end", f"[{ts}] ", "dim")
                _tag = tag
                if not tag and not is_end:
                    _tag = (
                        "err"
                        if any(
                            w in msg.lower()
                            for w in ("error", "exception", "traceback", "critical")
                        )
                        else "ok"
                        if any(
                            w in msg.lower() for w in ("started", "ready", "listening", "running")
                        )
                        else ""
                    )
                self._log.insert("end", msg.rstrip() + "\n", _tag or "")
            self._log.see("end")
            self._log.config(state="disabled")

        self._safe_after(0, _do)

    def _clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    # ── Button handlers ───────────────────────────────────
    def _on_start(self):
        self.controller.on_start()

    def _on_stop(self):
        self.controller.on_stop()

    def _on_restart(self):
        self.controller.on_restart()

    def _on_open(self):
        self.controller.on_open()

    def _on_kill_conflict(self):
        self.controller.on_kill_conflict()

    def _wait_for_server_ready(self, port):
        self.controller.wait_for_server_ready(port)

    def destroy(self):
        self._closing = True
        if self._is_running():
            try:
                if self.server_process:
                    self.server_process.stop()
            except Exception:
                pass
        super().destroy()

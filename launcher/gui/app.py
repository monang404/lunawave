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
    - launcher.server_lifecycle
    - launcher.gui.log_view
    - launcher.gui.popups
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
import tkinter as tk
import webbrowser
from pathlib import Path

import structlog

from launcher import network

# PATCH-2026-07-28 (temuan #9, P4-T1c): launcher/ adalah entry-point, tidak
# ada risiko circular-import. Konvensi mengikuti launcher/preflight.py --
# GUI ini tidak punya sistem logging sendiri sebelumnya (beda dari
# server_lifecycle.py yang report lewat callback on_log ke panel log GUI;
# titik-titik di file ini murni kegagalan level Tk/OS, di luar jalur itu).
logger = structlog.get_logger(component="launcher.gui.app")

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

        self._log_lock = threading.Lock()
        self._conflict_pid = None
        self._last_stdout_line = ""
        self._closing = False

        self._btn_start = None
        self._btn_stop = None
        self._btn_restart = None
        self._btn_open = None
        self._btn_dashboard = None
        self._port_entry = None
        self._btn_kill_conflict = None
        self._pid_label = None
        self._dot = None
        self._status_label = None
        self._log = None
        self._deps_status = None

        self._port_var = tk.StringVar(value=str(SERVER_PORT))

        from launcher.server_lifecycle import ServerLifecycle

        self.lifecycle = ServerLifecycle(
            BASE_DIR,
            on_log=self._write_log,
            on_ready=self._on_server_ready,
            on_deps_checked=self._on_deps_checked,
        )

        self._build_window()
        self._build_ui()
        self.lifecycle.run_dependency_check()
        self._refresh_status()

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

        # Klasifikasi: best-effort cleanup. Gagal load icon window tidak
        # boleh menggagalkan startup GUI -- window cuma tampil tanpa icon
        # custom. Debug-level untuk membantu diagnosis platform tertentu.
        try:
            icon_path = BASE_DIR / "web" / "static" / "icons" / "icon-512.png"
            if icon_path.exists():
                img = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, img)
            else:
                self.iconbitmap(default="")
        except Exception as e:
            logger.debug("window_icon_load_failed", error=str(e))

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
        # Klasifikasi: SENGAJA TETAP SILENT -- lihat docstring method ini
        # di atas (PATCH-2026-07-16-002) untuk alasan lengkapnya. Exception
        # type sudah dipersempit ke RuntimeError/TclError (bukan bare
        # Exception), jadi tidak menelan kelas error lain yang tak terduga.
        try:
            self.after(delay, callback)
        except (RuntimeError, tk.TclError):
            # RuntimeError/TclError sengaja dibiarkan (lihat docstring)
            pass

    # ── Dependency Checker callback (check runs in ServerLifecycle) ────
    def _on_deps_checked(self, missing, mpv_ok):
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

    # ── Server-ready callback (polling runs in ServerLifecycle) ────────
    def _on_server_ready(self, port):
        def _show_popup():
            from launcher.gui.popups import show_server_ready_popup

            show_server_ready_popup(self, port, BG, ACCENT, TEXT_1, TEXT_2, GREEN, BORDER, BG_CARD)

        self._safe_after(0, _show_popup)

    # ── Status ────────────────────────────────────────────
    def _is_running(self) -> bool:
        return self.lifecycle.is_running()

    def _refresh_status(self):
        if self._closing:
            return
        port = self.server_port
        running = self._is_running()

        if running:
            status = "RUNNING"
            color = GREEN
            self._pid_label.config(
                text=f"PID {self.lifecycle.server_process.process.pid}  ·  :{port}"
            )
            self._btn_start.config(state="disabled")
            self._btn_stop.config(state="normal")
            self._btn_restart.config(state="normal")
            self._btn_open.config(state="normal")
            self._btn_dashboard.config(state="normal")
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
                self._btn_dashboard.config(state="disabled")
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
                self._btn_dashboard.config(state="disabled")
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
        from launcher.gui.log_view import write_log

        write_log(self._log, self._safe_after, msg, tag, is_end)

    def _clear_log(self):
        from launcher.gui.log_view import clear_log

        clear_log(self._log)

    # ── Button handlers (thin: delegate to ServerLifecycle, then
    #    refresh the UI to reflect the new state) ──────────────────
    def _on_start(self):
        self.lifecycle.start(self.server_port)
        self._refresh_status()

    def _on_stop(self):
        self.lifecycle.stop()
        self._refresh_status()

    def _on_restart(self):
        self.lifecycle.restart(self.server_port)
        self._refresh_status()

    def _on_open(self):
        webbrowser.open(f"http://localhost:{self.server_port}")

    def _on_open_dashboard(self):
        webbrowser.open(f"http://localhost:{self.server_port}/admin/logs")

    def _on_kill_conflict(self):
        self.lifecycle.kill_conflict(self.server_port)
        self._refresh_status()

    def destroy(self):
        self._closing = True
        if self._is_running():
            # Klasifikasi: best-effort cleanup. Window sedang ditutup --
            # kalau stop() gagal, tidak ada yang bisa dilakukan lagi selain
            # lanjut ke super().destroy(). Debug-level untuk membantu
            # diagnosis proses server yang nyangkut saat GUI ditutup.
            try:
                self.lifecycle.server_process.stop()
            except Exception as e:
                logger.debug("shutdown_stop_failed", error=str(e))
        super().destroy()

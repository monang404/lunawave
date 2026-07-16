"""
Module: launcher.gui.controller

Purpose:
    Controls the underlying server lifecycle from within the launcher GUI.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - launcher
    - launcher.gui.popups

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread.
"""

import threading
import time
import webbrowser

from launcher import network, process


class ServerController:
    def __init__(self, app, base_dir):
        self.app = app
        self.BASE_DIR = base_dir

    def on_start(self):
        if self.app._is_running():
            return

        port = self.app.server_port

        # Ensure clean slate for mpv
        process.kill_mpv()

        if network.check_port_in_use(port):
            self.app._write_log(
                f"Port {port} is in use. Attempting to kill conflicting process...", "accent"
            )
            pid = network.get_pid_occupying_port(port)
            if pid:
                process.kill_process_tree(pid)
                time.sleep(1)
            if network.check_port_in_use(port):
                self.app._write_log(
                    f"Cannot start: Port {port} is still in use after kill attempt.", "err"
                )
                self.app._refresh_status()
                return

        self.app._write_log(f"Starting server on port {port}...", "accent")

        self.app.server_process = process.ServerProcess(
            str(self.BASE_DIR), port, on_log=self.app._write_log
        )
        try:
            self.app.server_process.start()
            self.app._write_log(
                f"Server process created — PID {self.app.server_process.process.pid}", "ok"
            )

            # Start thread to poll port and show popup when server is fully ready
            threading.Thread(target=self.wait_for_server_ready, args=(port,), daemon=True).start()
        except Exception as e:
            self.app._write_log(f"Failed to start: {e}", "err")

        self.app._refresh_status()

    def wait_for_server_ready(self, port: int):
        self.app._write_log("Waiting for server to bind and listen...", "dim")
        self.app._last_stdout_line = ""
        start_time = time.time()
        success = False
        while time.time() - start_time < 120:  # wait up to 120 seconds (2 minutes)
            if not self.app._is_running():
                break
            if network.check_port_in_use(port):
                success = True
                break
            time.sleep(0.5)

        if success:
            self.app._write_log(f"Server is fully active and listening on port {port}!", "ok")

            def _show_popup():
                from launcher.gui.popups import show_server_ready_popup

                show_server_ready_popup(
                    self.app,
                    port,
                    self.app.BG,
                    self.app.ACCENT,
                    self.app.TEXT_1,
                    self.app.TEXT_2,
                    self.app.GREEN,
                    self.app.BORDER,
                    self.app.BG_CARD,
                )

            self.app._safe_after(0, _show_popup)
        else:
            if not self.app._is_running():
                self.app._write_log("Server process terminated unexpectedly.", "err")
            else:
                self.app._write_log(
                    "Server failed to respond on port in time (120s timeout).", "err"
                )

    def on_stop(self):
        if not self.app._is_running():
            return
        self.app._write_log("Stopping server...", "accent")
        try:
            threading.Thread(target=self.wait_stop, daemon=True).start()
        except Exception as e:
            self.app._write_log(f"Error terminating: {e}", "err")

    def wait_stop(self):
        try:
            if self.app.server_process:
                self.app.server_process.stop()
        except Exception as e:
            self.app._write_log(f"Force killed: {e}", "err")

    def on_restart(self):
        self.app._write_log("Restarting...", "accent")

        def _do():
            if self.app._is_running():
                if self.app.server_process:
                    self.app.server_process.stop()
            time.sleep(0.8)
            self.app._safe_after(0, self.on_start)

        threading.Thread(target=_do, daemon=True).start()

    def on_open(self):
        port = self.app.server_port
        webbrowser.open(f"http://localhost:{port}")

    def on_kill_conflict(self):
        pid = getattr(self, "_conflict_pid", None)
        port = self.app.server_port
        if not pid:
            pid = network.get_pid_occupying_port(port)

        if pid:
            self.app._write_log(f"Killing process tree using port {port} (PID {pid})...", "accent")
            process.kill_process_tree(pid)
            time.sleep(0.8)
            if not network.check_port_in_use(port):
                self.app._write_log(f"Port {port} successfully cleared!", "ok")
            else:
                self.app._write_log(f"Failed to clear port {port}.", "err")
        else:
            self.app._write_log(f"Cannot identify PID for port {port}.", "err")

        self.app._refresh_status()

    # ── Clean exit ────────────────────────────────────────

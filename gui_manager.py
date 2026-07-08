import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import os
import secrets
import subprocess
import threading
import time
import webbrowser
import shutil
import socket
from pathlib import Path

# Constants from start.py
BASE_DIR   = Path(__file__).parent
SERVER_PORT = int(os.environ.get("LUNAWAVE_PORT", 8765))
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

from start import DependencyChecker, ServerProcessManager

class ServerReadyDialog(tk.Toplevel):
    def __init__(self, parent, port: int):
        super().__init__(parent)
        self.title("Server Ready")
        self.geometry("380x200")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        x = self.winfo_x() + (self.winfo_width() - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

        tk.Label(
            self, text="🚀 Server Berhasil Dijalankan!",
            bg=BG, fg=GREEN, font=("Segoe UI", 12, "bold"),
            pady=15
        ).pack()

        tk.Label(
            self,
            text=f"Server LunaWave aktif pada port {port}.\nSilakan login untuk mengelola musik.",
            bg=BG, fg=TEXT_2, font=("Segoe UI", 10),
            justify="center"
        ).pack(pady=(0, 15))

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(pady=10)

        btn_login = tk.Button(
            btn_frame, text="🔑 Buka Halaman Login", bg=ACCENT, fg=BG,
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
            cursor="hand2", padx=14, pady=6,
            command=lambda: [webbrowser.open(f"http://localhost:{port}/admin"), self.destroy()]
        )
        btn_login.pack(side="left", padx=5)

        btn_close = tk.Button(
            btn_frame, text="Tutup", bg=BG_CARD, fg=TEXT_2,
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
            cursor="hand2", padx=14, pady=6,
            command=self.destroy
        )
        btn_close.pack(side="left", padx=5)

        def on_enter_login(e): btn_login.config(bg=TEXT_1)
        def on_leave_login(e): btn_login.config(bg=ACCENT)
        btn_login.bind("<Enter>", on_enter_login)
        btn_login.bind("<Leave>", on_leave_login)

        def on_enter_close(e): btn_close.config(bg=BORDER, fg=TEXT_1)
        def on_leave_close(e): btn_close.config(bg=BG_CARD, fg=TEXT_2)
        btn_close.bind("<Enter>", on_enter_close)
        btn_close.bind("<Leave>", on_leave_close)


class PasswordResetDialog(tk.Toplevel):
    def __init__(self, parent, raw_password: str, is_first_run: bool = False):
        super().__init__(parent)
        self.title("Password Admin" if is_first_run else "Password Admin Baru")
        self.geometry("400x240")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 240) // 2
        self.geometry(f"+{x}+{y}")

        title_text = "🔑 Password Admin Dibuat Otomatis" if is_first_run else "🔑 Password Admin Berhasil Direset"
        tk.Label(
            self, text=title_text,
            bg=BG, fg=ACCENT, font=("Segoe UI", 12, "bold"),
            pady=10
        ).pack()

        warning_label = tk.Label(
            self,
            text="Simpan password ini baik-baik!\nPassword ini tidak akan ditampilkan lagi setelah jendela ini ditutup.",
            bg=BG, fg=RED, font=("Segoe UI", 9, "italic"),
            justify="center"
        )
        warning_label.pack(pady=(0, 10))

        frame = tk.Frame(self, bg=BG_CARD, padx=10, pady=10, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="x", padx=20, pady=5)

        tk.Label(frame, text="Username: admin", bg=BG_CARD, fg=TEXT_2, font=("Segoe UI", 9)).pack(anchor="w")

        pass_frame = tk.Frame(frame, bg=BG_CARD)
        pass_frame.pack(fill="x", pady=(5, 0))

        entry = tk.Entry(
            pass_frame, bg=BG_SURFACE, fg=TEXT_1,
            font=("Consolas", 11, "bold"), relief="flat",
            highlightthickness=0
        )
        entry.insert(0, raw_password)
        entry.config(state="readonly")
        entry.pack(side="left", fill="x", expand=True, ipady=4)

        def copy_pass():
            self.clipboard_clear()
            self.clipboard_append(raw_password)
            btn_copy.config(text="✓ Copied", fg=GREEN)
            self.after(2000, lambda: btn_copy.config(text="📋 Copy", fg=TEXT_1))

        btn_copy = tk.Button(
            pass_frame, text="📋 Copy", bg=BG_CARD, fg=TEXT_1,
            font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
            cursor="hand2", command=copy_pass, padx=8
        )
        btn_copy.pack(side="right", padx=(5, 0))

        btn_close = tk.Button(
            self, text="Tutup", bg=ACCENT, fg=BG,
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
            cursor="hand2", command=self.destroy, padx=20, pady=5
        )
        btn_close.pack(pady=15)


class ServerManagerController:
    def __init__(self, view):
        self.view = view
        self.pm = ServerProcessManager(BASE_DIR, PYTHON)
        self.dc = DependencyChecker()
        self._conflict_pid = None
        
    def run_dependency_check(self):
        def _thread_fn():
            missing, mpv_ok = self.dc.check_dependencies()
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
            self.view.update_deps_status(status_text, color)
        threading.Thread(target=_thread_fn, daemon=True).start()

    def check_first_run(self):
        password_file = BASE_DIR / "cache" / "admin_password.txt"
        if not password_file.exists():
            try:
                from core.security import hash_password
                raw_password = secrets.token_urlsafe(12)
                hashed_password = hash_password(raw_password)
                password_file.parent.mkdir(parents=True, exist_ok=True)
                with open(password_file, "w", encoding="utf-8") as f:
                    f.write(hashed_password)
                try:
                    import stat
                    password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
                except OSError:
                    pass
                self.view.after(500, lambda: self.view.show_new_password_dialog(raw_password, is_first_run=True))
            except Exception as e:
                self.view.write_log(f"First-run check failed: {e}", "err")

    def refresh_status(self):
        port = self.view.server_port
        running = self.pm.is_running()

        if running:
            status = "RUNNING"
            color = GREEN
            self.view.update_running_state(port, self.pm.process.pid, status, color)
        else:
            in_use = False
            conflict_pid = None
            if self.pm.check_port_in_use(port):
                in_use = True
                conflict_pid = self.pm.get_pid_occupying_port(port)

            if in_use:
                status = "CONFLICT"
                color = ACCENT
                self._conflict_pid = conflict_pid
                self.view.update_conflict_state(port, conflict_pid, status, color)
            else:
                status = "STOPPED"
                color = RED
                self.view.update_stopped_state(port, status, color)

        self.view.after(2000, self.refresh_status)

    def on_start(self):
        if self.pm.is_running():
            return
        port = self.view.server_port

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

        if self.pm.check_port_in_use(port):
            self.view.write_log(f"Port {port} is in use. Attempting to kill conflicting process...", "accent")
            pid = self.pm.get_pid_occupying_port(port)
            if pid:
                self.pm.kill_process_tree(pid)
                time.sleep(1)
            if self.pm.check_port_in_use(port):
                self.view.write_log(f"Cannot start: Port {port} is still in use after kill attempt.", "err")
                self.refresh_status()
                return

        self.view.write_log(f"Starting server on port {port}...", "accent")
        env = os.environ.copy()
        env["LUNAWAVE_HOST"] = "0.0.0.0"
        env["LUNAWAVE_PORT"] = str(port)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs["preexec_fn"] = os.setsid

        try:
            def on_log(line, tag):
                                self.view.write_log(line, tag)
            self.pm.start(port, env, on_log_cb=on_log)
            self.view.write_log(f"Server process created — PID {self.pm.process.pid}", "ok")
            threading.Thread(target=self._wait_for_server_ready, args=(port,), daemon=True).start()
        except Exception as e:
            self.view.write_log(f"Failed to start: {e}", "err")

        self.refresh_status()

    def _wait_for_server_ready(self, port: int):
        self.view.write_log("Waiting for server to bind and listen...", "dim")
        start_time = time.time()
        success = False
        while time.time() - start_time < 120:
            if not self.pm.is_running():
                break
            if self.pm.check_port_in_use(port):
                success = True
                break
            time.sleep(0.5)

        if success:
            self.view.write_log(f"Server is fully active and listening on port {port}!", "ok")
            self.view.after(0, lambda: self.view.show_server_ready_popup(port))
        else:
            if not self.pm.is_running():
                self.view.write_log("Server process terminated unexpectedly.", "err")
            else:
                self.view.write_log("Server failed to respond on port in time (120s timeout).", "err")

    def on_stop(self):
        if not self.pm.is_running():
            return
        self.view.write_log("Stopping server...", "accent")
        try:
            self.pm.kill_process_tree(self.pm.process.pid)
            threading.Thread(target=self.pm.wait_stop, daemon=True).start()
        except Exception as e:
            self.view.write_log(f"Error terminating: {e}", "err")

    def on_restart(self):
        self.view.write_log("Restarting...", "accent")
        def _do():
            if self.pm.is_running():
                try:
                    self.pm.kill_process_tree(self.pm.process.pid)
                    self.pm.wait_stop()
                except Exception:
                    pass
            time.sleep(0.8)
            self.view.after(0, self.on_start)
        threading.Thread(target=_do, daemon=True).start()

    def on_open(self):
        port = self.view.server_port
        webbrowser.open(f"http://localhost:{port}")

    def on_kill_conflict(self):
        pid = self._conflict_pid
        port = self.view.server_port
        if not pid:
            pid = self.pm.get_pid_occupying_port(port)

        if pid:
            self.view.write_log(f"Killing process tree using port {port} (PID {pid})...", "accent")
            self.pm.kill_process_tree(pid)
            time.sleep(0.8)
            if not self.pm.check_port_in_use(port):
                self.view.write_log(f"Port {port} successfully cleared!", "ok")
            else:
                self.view.write_log(f"Failed to clear port {port}.", "err")
        else:
            self.view.write_log(f"Cannot identify PID for port {port}.", "err")
        self.refresh_status()

    def on_reset_password(self):
        if not messagebox.askyesno("Reset Password", "Apakah Anda yakin ingin mereset password admin? Ini akan menimpa password yang ada."):
            return

        try:
            from core.security import hash_password
            raw_password = secrets.token_urlsafe(12)
            hashed_password = hash_password(raw_password)

            password_file = BASE_DIR / "data" / "admin_password.txt"
            password_file.parent.mkdir(parents=True, exist_ok=True)
            with open(password_file, "w", encoding="utf-8") as f:
                f.write(hashed_password)
            try:
                import stat
                password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass

            import sqlite3
            db_path = BASE_DIR / "data" / "lunawave.db"
            if db_path.exists():
                try:
                    conn = sqlite3.connect(db_path)
                    conn.execute("DELETE FROM sessions")
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

            self.view.show_new_password_dialog(raw_password)
            self.view.write_log("Admin password has been reset successfully.", "ok")
        except Exception as e:
            self.view.write_log(f"Error resetting password: {e}", "err")

    def on_destroy(self):
        if self.pm.is_running():
            try:
                self.pm.kill_process_tree(self.pm.process.pid)
            except Exception:
                pass


class ServerManagerWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self._port_var = tk.StringVar(value=str(SERVER_PORT))
        self.controller = ServerManagerController(self)
        self._build_window()
        self._build_ui()

        self.controller.run_dependency_check()
        self.controller.refresh_status()
        self.controller.check_first_run()

    def _build_window(self):
        self.title("bagas.fm — Server Manager")
        self.geometry("600x680")
        self.minsize(520, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 600) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"+{x}+{y}")

        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_SURFACE, pady=14)
        header.pack(fill="x")

        tk.Label(
            header, text="bagas.fm",
            bg=BG_SURFACE, fg=ACCENT,
            font=("Segoe UI", 18, "bold"),
        ).pack()
        tk.Label(
            header, text="Server Manager",
            bg=BG_SURFACE, fg=TEXT_3,
            font=("Segoe UI", 9),
        ).pack()

        status_frame = tk.Frame(self, bg=BG_CARD, pady=12, padx=16)
        status_frame.pack(fill="x", padx=16, pady=(14, 0))

        left = tk.Frame(status_frame, bg=BG_CARD)
        left.pack(side="left")

        self._dot = tk.Canvas(
            left, width=10, height=10,
            bg=BG_CARD, highlightthickness=0
        )
        self._dot.pack(side="left", padx=(0, 8), pady=2)

        self._status_label = tk.Label(
            left, text="Checking...",
            bg=BG_CARD, fg=TEXT_2,
            font=("Segoe UI", 10, "bold"),
        )
        self._status_label.pack(side="left")

        port_frame = tk.Frame(status_frame, bg=BG_CARD)
        port_frame.pack(side="right")

        tk.Label(
            port_frame, text="Port:",
            bg=BG_CARD, fg=TEXT_3,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 4))

        self._port_entry = tk.Entry(
            port_frame, textvariable=self._port_var,
            bg=BG_SURFACE, fg=TEXT_1, font=("Consolas", 10),
            width=6, relief="flat", insertbackground=TEXT_1,
            justify="center", highlightthickness=1, highlightbackground=BORDER
        )
        self._port_entry.pack(side="left")

        self._pid_label = tk.Label(
            status_frame, text="",
            bg=BG_CARD, fg=TEXT_3,
            font=("Segoe UI", 9),
        )
        self._pid_label.pack(side="right", padx=(0, 12))

        self._btn_kill_conflict = tk.Button(
            status_frame, text="☠  Kill Conflict Process",
            fg=RED, bg="#2A0A0A", font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2", bd=0, padx=6, pady=4,
            command=self.controller.on_kill_conflict
        )

        btn_frame = tk.Frame(self, bg=BG, pady=10)
        btn_frame.pack(fill="x", padx=16)
        btn_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self._btn_start = self._make_btn(
            btn_frame, "▶  Start", ACCENT, "#2A1F06",
            self.controller.on_start, col=0
        )
        self._btn_stop = self._make_btn(
            btn_frame, "■  Stop", RED, "#2A0A0A",
            self.controller.on_stop, col=1
        )
        self._btn_restart = self._make_btn(
            btn_frame, "↺  Restart", TEXT_2, BG_CARD,
            self.controller.on_restart, col=2
        )
        self._btn_open = self._make_btn(
            btn_frame, "⬡  Open Portal", TEXT_2, BG_CARD,
            self.controller.on_open, col=3
        )

        admin_frame = tk.Frame(self, bg=BG_CARD, pady=10, padx=16)
        admin_frame.pack(fill="x", padx=16, pady=(4, 0))

        tk.Label(
            admin_frame, text="🔑 ADMIN CREDENTIALS",
            bg=BG_CARD, fg=TEXT_3, font=("Segoe UI", 8, "bold")
        ).pack(side="left", anchor="w")

        tk.Label(
            admin_frame, text="User: admin  ·  Pass: [Hashed]",
            bg=BG_CARD, fg=TEXT_2, font=("Segoe UI", 9)
        ).pack(side="left", padx=15)

        btn_reset = tk.Button(
            admin_frame, text="Reset Password",
            bg=BG_SURFACE, fg=ACCENT, font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2", bd=0,
            activebackground=BG_CARD, activeforeground=TEXT_1,
            padx=10, command=self.controller.on_reset_password
        )
        btn_reset.pack(side="right")

        def on_enter_reset(e): btn_reset.config(bg=BG, fg=TEXT_1)
        def on_leave_reset(e): btn_reset.config(bg=BG_SURFACE, fg=ACCENT)
        btn_reset.bind("<Enter>", on_enter_reset)
        btn_reset.bind("<Leave>", on_leave_reset)

        links_frame = tk.Frame(self, bg=BG_CARD, pady=10, padx=16)
        links_frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(
            links_frame, text="🌐 QUICK LINKS (CLICK TO OPEN)",
            bg=BG_CARD, fg=TEXT_3, font=("Segoe UI", 8, "bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        self._link_client = self._make_link(links_frame, "Client Portal", "/", 1, 0)
        self._link_admin = self._make_link(links_frame, "Admin Console", "/admin", 1, 1)
        self._link_health = self._make_link(links_frame, "System Health", "/health", 1, 2)
        self._link_metrics = self._make_link(links_frame, "Metrics API", "/metrics", 1, 3)

        deps_frame = tk.Frame(self, bg=BG_CARD, pady=10, padx=16)
        deps_frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(
            deps_frame, text="⚙️ ENVIRONMENT & DEPENDENCIES",
            bg=BG_CARD, fg=TEXT_3, font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(0, 6))

        self._deps_status = tk.Label(
            deps_frame, text="Checking environment dependencies...",
            bg=BG_CARD, fg=TEXT_2, font=("Segoe UI", 9),
            justify="left", anchor="w"
        )
        self._deps_status.pack(fill="x")

        log_header = tk.Frame(self, bg=BG, pady=0)
        log_header.pack(fill="x", padx=16, pady=(10, 0))
        tk.Label(
            log_header, text="LOG",
            bg=BG, fg=TEXT_3,
            font=("Segoe UI", 8, "bold"),
            anchor="w"
        ).pack(side="left")
        tk.Button(
            log_header, text="Clear",
            bg=BG, fg=TEXT_3,
            font=("Segoe UI", 8),
            relief="flat", cursor="hand2", bd=0,
            activebackground=BG, activeforeground=TEXT_2,
            command=self.clear_log
        ).pack(side="right")

        self._log = scrolledtext.ScrolledText(
            self,
            bg=BG_SURFACE, fg=TEXT_2,
            font=("Consolas", 8),
            relief="flat", bd=0,
            wrap="word",
            insertbackground=TEXT_2,
            selectbackground=ACCENT,
            state="disabled",
            padx=10, pady=8,
        )
        self._log.pack(fill="both", expand=True, padx=16, pady=(4, 16))
        self._log.tag_config("accent", foreground=ACCENT)
        self._log.tag_config("err",    foreground=RED)
        self._log.tag_config("ok",     foreground=GREEN)
        self._log.tag_config("dim",    foreground=TEXT_3)

    def _make_btn(self, parent, text, fg, bg, cmd, col):
        b = tk.Button(
            parent, text=text,
            fg=fg, bg=bg,
            font=("Segoe UI", 9, "bold"),
            relief="flat", bd=0, cursor="hand2",
            activeforeground=fg,
            activebackground=BG_CARD,
            padx=8, pady=8,
            command=cmd,
        )
        b.grid(row=0, column=col, padx=3, sticky="ew")

        def on_enter(e):
            if b["state"] != "disabled":
                b.config(bg=BORDER, fg=TEXT_1)
        def on_leave(e):
            if b["state"] != "disabled":
                b.config(bg=bg, fg=fg)
        b.bind("<Enter>", on_enter)
        b.bind("<Leave>", on_leave)
        return b

    def _make_link(self, parent, text, path, row, col):
        lbl = tk.Label(
            parent, text=text,
            bg=BG_CARD, fg=TEXT_2,
            font=("Segoe UI", 9, "underline"),
            cursor="hand2"
        )
        lbl.grid(row=row, column=col, padx=8, pady=2, sticky="w")

        def open_url(event):
            port = self.server_port
            url = f"http://localhost:{port}{path}"
            webbrowser.open(url)
            self.write_log(f"Opening link: {url}", "dim")

        def on_enter(event):
            lbl.config(fg=ACCENT)

        def on_leave(event):
            lbl.config(fg=TEXT_2)

        lbl.bind("<Button-1>", open_url)
        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)
        return lbl

    @property
    def server_port(self) -> int:
        try:
            return int(self._port_var.get().strip())
        except ValueError:
            return 8765

    def update_deps_status(self, text: str, color: str):
        self.after(0, lambda: self._deps_status.config(text=text, fg=color))

    def update_running_state(self, port: int, pid: int, status: str, color: str):
        self._pid_label.config(text=f"PID {pid}  ·  :{port}")
        self._btn_start.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._btn_restart.config(state="normal")
        self._btn_open.config(state="normal")
        self._port_entry.config(state="disabled")
        self._btn_kill_conflict.pack_forget()
        self._update_status_indicator(status, color)

    def update_conflict_state(self, port: int, conflict_pid: int | None, status: str, color: str):
        pid_text = f"PID {conflict_pid}" if conflict_pid else "Unknown PID"
        self._pid_label.config(text=f"Port :{port} used by {pid_text}")
        self._btn_start.config(state="disabled")
        self._btn_stop.config(state="disabled")
        self._btn_restart.config(state="disabled")
        self._btn_open.config(state="normal")
        self._port_entry.config(state="normal")
        self._btn_kill_conflict.config(text=f"☠  Kill Process (PID {conflict_pid})" if conflict_pid else "☠  Kill Port Owner")
        self._btn_kill_conflict.pack(side="right", padx=(5, 0))
        self._update_status_indicator(status, color)

    def update_stopped_state(self, port: int, status: str, color: str):
        self._pid_label.config(text=f"Port :{port}")
        self._btn_start.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._btn_restart.config(state="disabled")
        self._btn_open.config(state="disabled")
        self._port_entry.config(state="normal")
        self._btn_kill_conflict.pack_forget()
        self._update_status_indicator(status, color)

    def _update_status_indicator(self, status: str, color: str):
        self._dot.delete("all")
        self._dot.create_oval(1, 1, 9, 9, fill=color, outline="")
        self._status_label.config(text=status, fg=color)

    def write_log(self, msg: str, tag: str = ""):
        def _do():
            self._log.config(state="normal")
            ts = time.strftime("%H:%M:%S")
            self._log.insert("end", f"[{ts}] ", "dim")
            self._log.insert("end", msg.rstrip() + "\n", tag or "")
            self._log.see("end")
            self._log.config(state="disabled")
        self.after(0, _do)

    def clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    def show_server_ready_popup(self, port: int):
        ServerReadyDialog(self, port)

    def show_new_password_dialog(self, raw_password: str, is_first_run: bool = False):
        PasswordResetDialog(self, raw_password, is_first_run)

    def destroy(self):
        self.controller.on_destroy()
        super().destroy()


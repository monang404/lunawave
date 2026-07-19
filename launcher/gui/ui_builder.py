"""
Module: launcher.gui.ui_builder

Purpose:
    Constructs the main user interface layout and elements for the launcher.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - launcher.gui.auth_panel

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread.
"""

import tkinter as tk
import webbrowser
from tkinter import scrolledtext

from launcher.gui.auth_panel import on_reset_password


class UIBuilder:
    def __init__(
        self, bg, bg_surface, bg_card, accent, text_1, text_2, text_3, green, red, border, base_dir
    ):
        self.BG = bg
        self.BG_SURFACE = bg_surface
        self.BG_CARD = bg_card
        self.ACCENT = accent
        self.TEXT_1 = text_1
        self.TEXT_2 = text_2
        self.TEXT_3 = text_3
        self.GREEN = green
        self.RED = red
        self.BORDER = border
        self.BASE_DIR = base_dir

    # ── UI Layout ─────────────────────────────────────────
    def build_ui(self, app):
        self._build_header(app)
        self._build_status_bar(app)
        self._build_controls(app)
        self._build_log_panel(app)

    def _build_header(self, app):
        header = tk.Frame(app, bg=self.BG_SURFACE, pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text="LunaWave",
            bg=self.BG_SURFACE,
            fg=self.ACCENT,
            font=("Segoe UI", 18, "bold"),
        ).pack()
        tk.Label(
            header,
            text="Server Manager",
            bg=self.BG_SURFACE,
            fg=self.TEXT_3,
            font=("Segoe UI", 9),
        ).pack()

    def _build_status_bar(self, app):
        # ── Status Card ──
        status_frame = tk.Frame(app, bg=self.BG_CARD, pady=12, padx=16)
        status_frame.pack(fill="x", padx=16, pady=(14, 0))

        left = tk.Frame(status_frame, bg=self.BG_CARD)
        left.pack(side="left")

        app._dot = tk.Canvas(left, width=10, height=10, bg=self.BG_CARD, highlightthickness=0)
        app._dot.pack(side="left", padx=(0, 8), pady=2)

        app._status_label = tk.Label(
            left,
            text="Checking...",
            bg=self.BG_CARD,
            fg=self.TEXT_2,
            font=("Segoe UI", 10, "bold"),
        )
        app._status_label.pack(side="left")

        # Port configuration input inside Status Frame
        port_frame = tk.Frame(status_frame, bg=self.BG_CARD)
        port_frame.pack(side="right")

        tk.Label(
            port_frame,
            text="Port:",
            bg=self.BG_CARD,
            fg=self.TEXT_3,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 4))

        app._port_entry = tk.Entry(
            port_frame,
            textvariable=app._port_var,
            bg=self.BG_SURFACE,
            fg=self.TEXT_1,
            font=("Consolas", 10),
            width=6,
            relief="flat",
            insertbackground=self.TEXT_1,
            justify="center",
            highlightthickness=1,
            highlightbackground=self.BORDER,
        )
        app._port_entry.pack(side="left")

        app._pid_label = tk.Label(
            status_frame,
            text="",
            bg=self.BG_CARD,
            fg=self.TEXT_3,
            font=("Segoe UI", 9),
        )
        app._pid_label.pack(side="right", padx=(0, 12))

        # Conflict action panel (Kill conflicting process)
        app._btn_kill_conflict = tk.Button(
            status_frame,
            text="☠  Kill Conflict Process",
            fg=self.RED,
            bg="#2A0A0A",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=6,
            pady=4,
            command=app._on_kill_conflict,
        )

    def _build_controls(self, app):
        # ── Buttons ──
        btn_frame = tk.Frame(app, bg=self.BG, pady=10)
        btn_frame.pack(fill="x", padx=16)
        btn_frame.columnconfigure((0, 1, 2, 3), weight=1)

        app._btn_start = self._make_btn(
            btn_frame, "▶  Start", self.ACCENT, "#2A1F06", app._on_start, col=0
        )
        app._btn_stop = self._make_btn(
            btn_frame, "■  Stop", self.RED, "#2A0A0A", app._on_stop, col=1
        )
        app._btn_restart = self._make_btn(
            btn_frame, "↺  Restart", self.TEXT_2, self.BG_CARD, app._on_restart, col=2
        )
        app._btn_open = self._make_btn(
            btn_frame, "⬡  Open Portal", self.TEXT_2, self.BG_CARD, app._on_open, col=3
        )

        # ── Admin Credentials Frame ──
        admin_frame = tk.Frame(app, bg=self.BG_CARD, pady=10, padx=16)
        admin_frame.pack(fill="x", padx=16, pady=(4, 0))

        tk.Label(
            admin_frame,
            text="🔑 ADMIN CREDENTIALS",
            bg=self.BG_CARD,
            fg=self.TEXT_3,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left", anchor="w")

        tk.Label(
            admin_frame,
            text="User: admin  ·  Pass: [Hashed]",
            bg=self.BG_CARD,
            fg=self.TEXT_2,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=15)

        btn_reset = tk.Button(
            admin_frame,
            text="Reset Password",
            bg=self.BG_SURFACE,
            fg=self.ACCENT,
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_1,
            padx=10,
            command=lambda: on_reset_password(
                app,
                self.BASE_DIR,
                self.BG,
                self.BG_CARD,
                self.BG_SURFACE,
                self.ACCENT,
                self.TEXT_1,
                self.TEXT_2,
                self.TEXT_3,
                self.RED,
                self.GREEN,
                self.BORDER,
            ),
        )
        btn_reset.pack(side="right")

        # Hover effect for reset button
        def on_enter_reset(e):
            btn_reset.config(bg=self.BG, fg=self.TEXT_1)

        def on_leave_reset(e):
            btn_reset.config(bg=self.BG_SURFACE, fg=self.ACCENT)

        btn_reset.bind("<Enter>", on_enter_reset)
        btn_reset.bind("<Leave>", on_leave_reset)

        # ── Quick Links Frame ──
        links_frame = tk.Frame(app, bg=self.BG_CARD, pady=10, padx=16)
        links_frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(
            links_frame,
            text="🌐 QUICK LINKS (CLICK TO OPEN)",
            bg=self.BG_CARD,
            fg=self.TEXT_3,
            font=("Segoe UI", 8, "bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        app._link_client = self._make_link(app, links_frame, "Client Portal", "/", 1, 0)
        app._link_admin = self._make_link(app, links_frame, "Admin Console", "/admin", 1, 1)
        app._link_health = self._make_link(app, links_frame, "System Health", "/health", 1, 2)
        app._link_metrics = self._make_link(app, links_frame, "Metrics API", "/metrics", 1, 3)

        # ── Dependencies Frame ──
        deps_frame = tk.Frame(app, bg=self.BG_CARD, pady=10, padx=16)
        deps_frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(
            deps_frame,
            text="⚙️ ENVIRONMENT & DEPENDENCIES",
            bg=self.BG_CARD,
            fg=self.TEXT_3,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        app._deps_status = tk.Label(
            deps_frame,
            text="Checking environment dependencies...",
            bg=self.BG_CARD,
            fg=self.TEXT_2,
            font=("Segoe UI", 9),
            justify="left",
            anchor="w",
        )
        app._deps_status.pack(fill="x")

    def _build_log_panel(self, app):
        # ── Log area ──
        log_header = tk.Frame(app, bg=self.BG, pady=0)
        log_header.pack(fill="x", padx=16, pady=(10, 0))
        tk.Label(
            log_header,
            text="LOG",
            bg=self.BG,
            fg=self.TEXT_3,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).pack(side="left")
        tk.Button(
            log_header,
            text="Clear",
            bg=self.BG,
            fg=self.TEXT_3,
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            bd=0,
            activebackground=self.BG,
            activeforeground=self.TEXT_2,
            command=app._clear_log,
        ).pack(side="right")

        app._log = scrolledtext.ScrolledText(
            app,
            bg=self.BG_SURFACE,
            fg=self.TEXT_2,
            font=("Consolas", 8),
            relief="flat",
            bd=0,
            wrap="word",
            insertbackground=self.TEXT_2,
            selectbackground=self.ACCENT,
            state="disabled",
            padx=10,
            pady=8,
        )
        app._log.pack(fill="both", expand=True, padx=16, pady=(4, 16))
        app._log.tag_config("accent", foreground=self.ACCENT)
        app._log.tag_config("err", foreground=self.RED)
        app._log.tag_config("ok", foreground=self.GREEN)
        app._log.tag_config("dim", foreground=self.TEXT_3)

    def _make_btn(self, parent, text, fg, bg, cmd, col):
        b = tk.Button(
            parent,
            text=text,
            fg=fg,
            bg=bg,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            activeforeground=fg,
            activebackground=self.BG_CARD,
            padx=8,
            pady=8,
            command=cmd,
        )
        b.grid(row=0, column=col, padx=3, sticky="ew")

        def on_enter(e):
            if b["state"] != "disabled":
                b.config(bg=self.BORDER, fg=self.TEXT_1)

        def on_leave(e):
            if b["state"] != "disabled":
                b.config(bg=bg, fg=fg)

        b.bind("<Enter>", on_enter)
        b.bind("<Leave>", on_leave)
        return b

    def _make_link(self, app, parent, text, path, row, col):
        lbl = tk.Label(
            parent,
            text=text,
            bg=self.BG_CARD,
            fg=self.TEXT_2,
            font=("Segoe UI", 9, "underline"),
            cursor="hand2",
        )
        lbl.grid(row=row, column=col, padx=8, pady=2, sticky="w")

        def open_url(event):
            port = app.server_port
            url = f"http://localhost:{port}{path}"
            webbrowser.open(url)
            app._write_log(f"Opening link: {url}", "dim")

        def on_enter(event):
            lbl.config(fg=self.ACCENT)

        def on_leave(event):
            lbl.config(fg=self.TEXT_2)

        lbl.bind("<Button-1>", open_url)
        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)
        return lbl

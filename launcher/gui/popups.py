"""
Module: launcher.gui.popups

Purpose:
    Helper module for displaying generic popup dialogs in the GUI.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

import tkinter as tk
import webbrowser


def show_server_ready_popup(parent, port: int, bg, accent, text_1, text_2, green, border, bg_card):
    # content from _show_server_ready_popup
    popup = tk.Toplevel(parent)
    popup.title("Server Ready")
    popup.geometry("380x200")
    popup.configure(bg=bg)
    popup.resizable(False, False)
    popup.transient(parent)
    popup.grab_set()

    # Center popup relative to main window
    x = parent.winfo_x() + (parent.winfo_width() - 380) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
    popup.geometry(f"+{x}+{y}")

    # Title
    tk.Label(
        popup,
        text="🚀 Server Berhasil Dijalankan!",
        bg=bg,
        fg=green,
        font=("Segoe UI", 12, "bold"),
        pady=15,
    ).pack()

    # Message
    tk.Label(
        popup,
        text=f"Server LunaWave aktif pada port {port}.\nSilakan login untuk mengelola room.",
        bg=bg,
        fg=text_2,
        font=("Segoe UI", 10),
        justify="center",
    ).pack(pady=(0, 15))

    # Action Buttons frame
    btn_frame = tk.Frame(popup, bg=bg)
    btn_frame.pack(pady=10)

    # Buka Halaman Login
    btn_login = tk.Button(
        btn_frame,
        text="🔑 Buka Halaman Login",
        bg=accent,
        fg=bg,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=14,
        pady=6,
        command=lambda: [webbrowser.open(f"http://localhost:{port}/admin"), popup.destroy()],  # type: ignore
    )
    btn_login.pack(side="left", padx=5)

    # Tutup button
    btn_close = tk.Button(
        btn_frame,
        text="Tutup",
        bg=bg_card,
        fg=text_2,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=14,
        pady=6,
        command=popup.destroy,
    )
    btn_close.pack(side="left", padx=5)

    # Hover effects
    def on_enter_login(e):
        btn_login.config(bg=text_1)

    def on_leave_login(e):
        btn_login.config(bg=accent)

    btn_login.bind("<Enter>", on_enter_login)
    btn_login.bind("<Leave>", on_leave_login)

    def on_enter_close(e):
        btn_close.config(bg=border, fg=text_1)

    def on_leave_close(e):
        btn_close.config(bg=bg_card, fg=text_2)

    btn_close.bind("<Enter>", on_enter_close)
    btn_close.bind("<Leave>", on_leave_close)

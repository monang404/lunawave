"""
Module: launcher.gui.auth_panel

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import secrets
import tkinter as tk
from tkinter import messagebox


# Need to know BASE_DIR, let's pass it
def handle_first_run(
    app_instance,
    base_dir,
    bg,
    bg_card,
    bg_surface,
    accent,
    text_1,
    text_2,
    text_3,
    red,
    green,
    border,
):
    password_file = base_dir / "cache" / "admin_password.txt"
    if not password_file.exists():
        _reset_password(
            app_instance,
            base_dir,
            True,
            bg,
            bg_card,
            bg_surface,
            accent,
            text_1,
            text_2,
            text_3,
            red,
            green,
            border,
        )


def on_reset_password(
    app_instance,
    base_dir,
    bg,
    bg_card,
    bg_surface,
    accent,
    text_1,
    text_2,
    text_3,
    red,
    green,
    border,
):
    if not messagebox.askyesno(
        "Reset Password",
        "Apakah Anda yakin ingin mereset password admin? Ini akan menimpa password yang ada.",
    ):
        return
    _reset_password(
        app_instance,
        base_dir,
        False,
        bg,
        bg_card,
        bg_surface,
        accent,
        text_1,
        text_2,
        text_3,
        red,
        green,
        border,
    )


def _reset_password(
    app_instance,
    base_dir,
    is_first_run,
    bg,
    bg_card,
    bg_surface,
    accent,
    text_1,
    text_2,
    text_3,
    red,
    green,
    border,
):
    try:
        try:
            from core.security import hash_password
        except ImportError:
            import base64
            import hashlib

            def hash_password(password: str) -> str:
                salt = secrets.token_bytes(16)
                key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
                return f"pbkdf2:sha256:100000${base64.b64encode(salt).decode('utf-8')}${base64.b64encode(key).decode('utf-8')}"

        raw_password = secrets.token_urlsafe(12)
        hashed_password = hash_password(raw_password)

        password_file = base_dir / "cache" / "admin_password.txt"
        password_file.parent.mkdir(parents=True, exist_ok=True)
        with open(password_file, "w", encoding="utf-8") as f:
            f.write(hashed_password)
        try:
            import stat

            password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

        if is_first_run:
            app_instance.after(
                500,
                lambda: show_new_password_dialog(
                    app_instance,
                    raw_password,
                    True,
                    bg,
                    bg_card,
                    bg_surface,
                    accent,
                    text_1,
                    text_2,
                    text_3,
                    red,
                    green,
                    border,
                ),
            )
        else:
            show_new_password_dialog(
                app_instance,
                raw_password,
                False,
                bg,
                bg_card,
                bg_surface,
                accent,
                text_1,
                text_2,
                text_3,
                red,
                green,
                border,
            )
            if hasattr(app_instance, "_write_log"):
                app_instance._write_log("Admin password has been reset successfully.", "ok")
    except Exception as e:
        if hasattr(app_instance, "_write_log"):
            app_instance._write_log(f"Error resetting password: {e}", "err")


def show_new_password_dialog(
    parent,
    raw_password,
    is_first_run,
    bg,
    bg_card,
    bg_surface,
    accent,
    text_1,
    text_2,
    text_3,
    red,
    green,
    border,
):
    dialog = tk.Toplevel(parent)
    dialog.title("Password Admin" if is_first_run else "Password Admin Baru")
    dialog.geometry("400x240")
    dialog.configure(bg=bg)
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 240) // 2
    dialog.geometry(f"+{x}+{y}")

    title_text = (
        "🔑 Password Admin Dibuat Otomatis"
        if is_first_run
        else "🔑 Password Admin Berhasil Direset"
    )
    tk.Label(
        dialog, text=title_text, bg=bg, fg=accent, font=("Segoe UI", 12, "bold"), pady=10
    ).pack()

    warning_label = tk.Label(
        dialog,
        text="Simpan password ini baik-baik!\nPassword ini tidak akan ditampilkan lagi setelah jendela ini ditutup.",
        bg=bg,
        fg=red,
        font=("Segoe UI", 9, "italic"),
        justify="center",
    )
    warning_label.pack(pady=(0, 10))

    frame = tk.Frame(
        dialog, bg=bg_card, padx=10, pady=10, highlightbackground=border, highlightthickness=1
    )
    frame.pack(fill="x", padx=20, pady=5)

    tk.Label(frame, text="Username: admin", bg=bg_card, fg=text_2, font=("Segoe UI", 9)).pack(
        anchor="w"
    )

    pass_frame = tk.Frame(frame, bg=bg_card)
    pass_frame.pack(fill="x", pady=(5, 0))

    entry = tk.Entry(
        pass_frame,
        bg=bg_surface,
        fg=text_1,
        font=("Consolas", 11, "bold"),
        relief="flat",
        highlightthickness=0,
    )
    entry.insert(0, raw_password)
    entry.config(state="readonly")
    entry.pack(side="left", fill="x", expand=True, ipady=4)

    def copy_pass():
        parent.clipboard_clear()
        parent.clipboard_append(raw_password)
        btn_copy.config(text="✓ Copied", fg=green)
        dialog.after(2000, lambda: btn_copy.config(text="📋 Copy", fg=text_1))

    btn_copy = tk.Button(
        pass_frame,
        text="📋 Copy",
        bg=bg_card,
        fg=text_1,
        font=("Segoe UI", 8, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        command=copy_pass,
        padx=8,
    )
    btn_copy.pack(side="right", padx=(5, 0))

    btn_close = tk.Button(
        dialog,
        text="Tutup",
        bg=accent,
        fg=bg,
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        command=dialog.destroy,
        padx=20,
        pady=5,
    )
    btn_close.pack(pady=15)

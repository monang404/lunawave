"""
Module: launcher.gui.auth_panel

Purpose:
    GUI hook for the "Reset Password" button. Since T-B16, the launcher no
    longer owns any authentication mechanism of its own — it only opens the
    web portal, where Initial Setup / Login (SQLite-backed admin_account,
    see server/handlers/setup.py) handles credentials end-to-end.

Responsibilities:
    - Open the web portal in the user's default browser when "Reset
      Password" is clicked, so the web UI's own setup/login flow can take
      over (K5).

Depends on:
    None. Uses app_instance.server_port (property already exposed by
    launcher.gui.app.ServerManager) to build the portal URL.

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread only (Tkinter / webbrowser calls).
"""

import webbrowser


def on_reset_password(app_instance):
    """Open the web portal so the user can (re)configure admin login there.

    The launcher has no local auth mechanism anymore (T-B16.1 removed
    launcher.auth_service and the instance/admin_password.txt file it used
    to read/write). "Reset Password" now just routes the user to the same
    SQLite-backed admin_account flow as everything else -- the web UI
    itself decides whether to show Initial Setup or Login (see
    server/handlers/setup.py, GET /api/setup-required).
    """
    url = f"http://localhost:{app_instance.server_port}"
    webbrowser.open(url)
    if hasattr(app_instance, "_write_log"):
        app_instance._write_log("Membuka portal web untuk setup/login admin...", "dim")

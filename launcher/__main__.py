"""
Module: launcher.__main__

Purpose:
    Entry point for the LunaWave launcher when executed as a package.

Inputs:
    None (no CLI arguments).

Outputs:
    Tkinter ServerManager GUI window.

Side Effects:
    Opens the desktop GUI; exits with code 1 if tkinter is unavailable.

CLI:
    python -m launcher

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

import sys


def main():
    try:
        import tkinter as tk  # noqa: F401
    except ImportError:
        print(
            "Tkinter is not available. Please run `python main.py` directly or use `start.sh` on headless environments like Termux.",
            file=sys.stderr,
        )
        sys.exit(1)

    from .gui import ServerManager

    app = ServerManager()
    app.mainloop()


if __name__ == "__main__":
    main()

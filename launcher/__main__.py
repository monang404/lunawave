import sys

def main():
    try:
        import tkinter as tk
    except ImportError:
        print("Tkinter is not available. Please run `python main.py` directly or use `start.sh` on headless environments like Termux.", file=sys.stderr)
        sys.exit(1)

    from .gui import ServerManager
    app = ServerManager()
    app.mainloop()

if __name__ == "__main__":
    main()

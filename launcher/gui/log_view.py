"""
Module: launcher.gui.log_view

Purpose:
    Render log lines and manage clearing of the launcher GUI's log widget.

Responsibilities:
    - Format and insert log lines (timestamp, color tag by keyword) into a
      Tkinter `ScrolledText` widget on the main thread.
    - Clear the log widget.

Depends on:
    None (operates on whatever text widget it is given)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    `write_log` may be called from any thread; the actual widget mutation
    is always marshaled onto the main thread via the `safe_after` callback
    passed in by the caller (Tkinter widgets are main-thread only).
    `clear_log` is only ever called directly from a button handler on the
    main thread, so it touches the widget synchronously.
"""

import time


def write_log(log_widget, safe_after, msg: str, tag: str = "", is_end: bool = False):
    def _do():
        log_widget.config(state="normal")
        if is_end:
            log_widget.insert("end", msg.rstrip() + "\n", "dim")
        else:
            ts = time.strftime("%H:%M:%S")
            log_widget.insert("end", f"[{ts}] ", "dim")
            _tag = tag
            if not tag and not is_end:
                _tag = (
                    "err"
                    if any(w in msg.lower() for w in ("error", "exception", "traceback", "critical"))
                    else "ok"
                    if any(w in msg.lower() for w in ("started", "ready", "listening", "running"))
                    else ""
                )
            log_widget.insert("end", msg.rstrip() + "\n", _tag or "")
        log_widget.see("end")
        log_widget.config(state="disabled")

    safe_after(0, _do)


def clear_log(log_widget):
    log_widget.config(state="normal")
    log_widget.delete("1.0", "end")
    log_widget.config(state="disabled")

import os
import threading
import sys
import time

try:
    import psutil
except ImportError:
    psutil = None

_R  = "\033[0m"
_G  = "\033[32m"
_Y  = "\033[33m"
_RE = "\033[31m"
_B  = "\033[34m"
_GY = "\033[90m"
_C  = "\033[36m"
_W  = "\033[1m"
_BG = "\033[1;32m"

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class _Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.songs_played = 0
        self.errors = 0
        self.timeouts = 0
        self.clients = 0
        self.current_track = "—"
        self.status = "Idle"
        self.queue_size = 0
        self.is_playing = False

    def inc(self, field, n=1):
        with self.lock:
            setattr(self, field, getattr(self, field) + n)

STATS = _Stats()

_status_bar_active = False
_status_bar_thread = None
_stop_event = threading.Event()
_summary_active = False
_summary_thread = None

def _status_bar_worker():
    proc = psutil.Process(os.getpid()) if psutil else None
    while _status_bar_active and not _stop_event.is_set():
        try:
            if proc is not None:
                ram_mb = int(proc.memory_info().rss / 1024 / 1024)
                cpu = proc.cpu_percent(interval=None)
            else:
                ram_mb = 0
                cpu = 0.0
        except Exception:
            ram_mb = 0
            cpu = 0.0

        with STATS.lock:
            clients = STATS.clients
            is_playing = STATS.is_playing
            queue = STATS.queue_size

        status_icon = "🎵" if is_playing else "⏸ "
        status_text = "Playing" if is_playing else "Paused"
        if STATS.status == "Idle":
            status_icon = "💤"
            status_text = "Idle"

        line = (
            f"\033[s"
            f"\033[999;1H"
            f"\033[2K"
            f"{_GY}────────────────────────────────────────────────────────{_R}\n"
            f"\033[2K"
            f" {_W}▸ LunaWave{_R}  "
            f"{_BG}🟢 Ready{_R}  "
            f"👤 {_C}{clients}{_R} client{'s' if clients != 1 else ''}  "
            f"{status_icon} {_G}{status_text}{_R}  "
            f"Queue {_Y}{queue}{_R}  "
            f"RAM {_GY}{ram_mb} MB{_R}  "
        )
        sys.stdout.write(line)
        sys.stdout.flush()
        
        sys.stdout.write(f"\033[u")
        sys.stdout.flush()

        time.sleep(1.0)

def _summary_worker():
    while _summary_active and not _stop_event.is_set():
        # Only print summary every 15 mins (if we wanted to). We'll leave it empty to avoid log spam,
        # or implement a small timer loop.
        for _ in range(900):
            if _stop_event.is_set() or not _summary_active:
                break
            time.sleep(1)
        if _stop_event.is_set() or not _summary_active:
            break
        with STATS.lock:
            import structlog
            logger = structlog.get_logger("stats")
            logger.info("system_stats",
                played=STATS.songs_played,
                errors=STATS.errors,
                timeouts=STATS.timeouts,
                clients=STATS.clients,
                queue=STATS.queue_size
            )

def start_ui_threads():
    global _status_bar_active, _status_bar_thread, _summary_active, _summary_thread
    if os.environ.get("LUNAWAVE_CLI_UI", "1") == "1":
        _status_bar_active = True
        _status_bar_thread = threading.Thread(target=_status_bar_worker, daemon=True)
        _status_bar_thread.start()

    _summary_active = True
    _summary_thread = threading.Thread(target=_summary_worker, daemon=True)
    _summary_thread.start()

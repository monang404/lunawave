import logging
import logging.handlers
import os
import sys
import time
import re

import structlog
from core.cli_ui import STATS, SPINNER_FRAMES, start_ui_threads

# ── ANSI colours ────────────────────────────────────────────
_R  = "\033[0m"
_G  = "\033[32m"
_Y  = "\033[33m"
_RE = "\033[31m"
_B  = "\033[34m"
_GY = "\033[90m"
_C  = "\033[36m"
_W  = "\033[1m"
_BG = "\033[1;32m"

class _CompactRenderer:
    def __init__(self):
        self.last_ts = ""

    def __call__(self, logger, name, event_dict):
        ts = event_dict.pop("timestamp", "")
        level = event_dict.pop("level", "").lower()
        exc = event_dict.pop("exc_info", None)
        req_id = event_dict.pop("request_id", "")
        
        # Colorize level
        lvl_col = _W
        if level in ("warning", "warn"): lvl_col = _Y
        elif level in ("error", "exception", "critical"): lvl_col = _RE
        elif level == "debug": lvl_col = _GY
        
        lvl_str = f"{lvl_col}{level.upper():<5}{_R}"

        msg = event_dict.pop("event", "")
        if "HTTP Request: " in str(msg):
            msg = f"{_GY}{msg}{_R}"
            
        req_str = f" {_GY}[{req_id[:8]}]{_R}" if req_id else ""

        # Extract remaining keys as dim context
        ctx_parts = []
        for k, v in event_dict.items():
            if k == "positional_args" and not v: continue
            ctx_parts.append(f"{_GY}{k}={v}{_R}")
        
        ctx_str = (" " + " ".join(ctx_parts)) if ctx_parts else ""
        
        out = f"{_GY}{ts}{_R} {lvl_str} {msg}{req_str}{ctx_str}"
        
        if exc:
            out += f"\n{_RE}{exc}{_R}"
            
        return out

class _FileFormatter(logging.Formatter):
    _ANSI_RE = re.compile(r"\033\[[0-9;]*m")
    
    def format(self, record):
        msg = super().format(record)
        return self._ANSI_RE.sub("", msg)

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=5*1024*1024,
        backupCount=2,
        encoding="utf-8"
    )
    
    file_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler.setFormatter(_FileFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    file_handler.setLevel(logging.DEBUG)

    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.server").setLevel(logging.WARNING)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _CompactRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # clear existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # Use a raw StreamHandler for structlog output to terminal
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    
    root_logger.addHandler(console)
    root_logger.addHandler(file_handler)
    
    start_ui_threads()

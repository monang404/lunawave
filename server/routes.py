"""
Constants for HTTP routes used in the server.
"""

ROUTE_INDEX = "/"
ROUTE_WS = "/ws"
ROUTE_STREAM = "/api/v1/stream/{video_id}"
ROUTE_HEALTH = "/health"
ROUTE_METRICS = "/metrics"
ROUTE_STATIC = "/static"

import os
from pathlib import Path
STATIC_DIR = Path(os.environ.get("LUNAWAVE_BASE", Path(__file__).parent.parent)) / "web" / "static"

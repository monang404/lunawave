import asyncio
import json
import os
import sys
import traceback
import urllib.request

import structlog

logger = structlog.get_logger(__name__)

def send_alert(message: str):
    webhook_url = os.environ.get("LUNAWAVE_ALERT_WEBHOOK")
    if not webhook_url:
        return
    try:
        req = urllib.request.Request(webhook_url, method="POST")
        req.add_header("Content-Type", "application/json")
        data = json.dumps({"content": f"🚨 **LunaWave Alert** 🚨\n```\n{message[:1900]}\n```"}).encode("utf-8")
        urllib.request.urlopen(req, data=data, timeout=5.0)
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    send_alert(f"Unhandled Exception: {exc_type.__name__}\n{tb_str}")

def handle_async_exception(loop, context):
    msg = context.get("exception", context["message"])
    logger.error(f"Caught asyncio exception: {msg}")
    send_alert(f"Asyncio Error: {msg}")

def setup_alerting():
    sys.excepthook = handle_exception
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_async_exception)
    except RuntimeError:
        pass

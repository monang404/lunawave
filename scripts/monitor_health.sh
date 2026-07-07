#!/bin/bash
# monitor_health.sh - Script to check if YTGUI is running and healthy
PORT=${LUNAWAVE_PORT:-8765}
HEALTH_URL="http://localhost:$PORT/health"
RES=$(curl -sf "$HEALTH_URL")

if [ $? -ne 0 ]; then
    if command -v termux-notification &> /dev/null; then
        termux-notification --title 'YTGUI DOWN' --content 'YTGUI Server is not reachable.'
    else
        echo "[!] YTGUI DOWN: Server is not reachable."
    fi
    exit 1
fi

STATUS=$(echo "$RES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))")
if [ "$STATUS" != "ok" ]; then
    if command -v termux-notification &> /dev/null; then
        termux-notification --title 'YTGUI DEGRADED' --content "Health degraded: $RES"
    else
        echo "[!] YTGUI DEGRADED: $RES"
    fi
else
    echo "[+] YTGUI is healthy."
fi

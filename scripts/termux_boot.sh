#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
termux-wake-lock
cd ~/ytgui-main || cd ~/ytgui-project || exit 1

# Pastikan direktori log ada
mkdir -p logs

# Jalankan di background dan simpan PID
./start.sh >> logs/startup.log 2>&1 &
STARTUP_PID=$!

# Tunggu sebentar dan verifikasi process masih hidup (S02-050)
sleep 3
if ! kill -0 "$STARTUP_PID" 2>/dev/null; then
    echo "[termux_boot] GAGAL: start.sh berhenti dalam 3 detik. Cek logs/startup.log" >> logs/startup.log
    exit 1
fi

echo "[termux_boot] Server berjalan dengan PID $STARTUP_PID" >> logs/startup.log

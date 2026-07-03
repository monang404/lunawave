#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/ytgui-main || cd ~/ytgui-project || exit
./start.sh >> logs/startup.log 2>&1 &

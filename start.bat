@echo off
color 0B
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo.
echo  _      _    _  _   _   ___   __    __   ___  __      __ _____
echo ^| ^|    ^| ^|  ^| ^|^| \ ^| ^| / _ \  \ \  / /  / _ \ \ \    / /^|  ___^|
echo ^| ^|    ^| ^|  ^| ^|^|  \ ^| ^|/ /_\ \  \ \/ /  / /_\ \ \ \  / / ^| ^|__
echo ^| ^|___ ^| ^|__^| ^|^| ^|\  ^|  ___  \  \  /\  /  ___  \ \ \/ /  ^|  __^|
echo ^|_____^| \____/^|_^| \_/_/_/   \_\  \/  \/_/_/   \_\  \__/   ^|_____^|
echo.
echo    ================================================================
echo                      LunaWave Web Server Startup
echo    ================================================================
echo.

:: ----------------------------------------------------------
::  CONFIGURATION
:: ----------------------------------------------------------
set "LUNAWAVE_HOST=0.0.0.0"
set "LUNAWAVE_PORT=8765"

:: support legacy environment variables if set
if defined YTGUI_HOST set "LUNAWAVE_HOST=%YTGUI_HOST%"
if defined YTGUI_PORT set "LUNAWAVE_PORT=%YTGUI_PORT%"
if defined YTGUI_ADMIN_USER set "LUNAWAVE_ADMIN_USER=%YTGUI_ADMIN_USER%"
if defined YTGUI_ADMIN_PASS set "LUNAWAVE_ADMIN_PASS=%YTGUI_ADMIN_PASS%"

:: ----------------------------------------------------------
::  STARTUP SEQUENCE
:: ----------------------------------------------------------

echo  [*] Initializing Environment Variables...

echo  [*] Checking Python Dependencies...
set "DEPS_OK=1"
python -c "import sys, importlib.util; missing = [m for m in ['aiohttp', 'aiosqlite', 'yt_dlp', 'syncedlyrics', 'structlog', 'prometheus_client', 'opentelemetry'] if importlib.util.find_spec(m) is None]; sys.exit(1 if missing else 0)" > nul 2>&1
if errorlevel 1 (
    echo      [-] Ada modul yang belum terinstall.
    echo          Jalankan: pip install -r requirements.txt
    set "DEPS_OK=0"
)

if "%DEPS_OK%"=="1" (
    echo      [+] All Python dependencies are satisfied.
) else (
    echo.
    echo  [!] WARNING: Some dependencies are missing.
    echo      Please run: pip install -r requirements.txt
    echo.
    ping 127.0.0.1 -n 4 > nul
)

echo  [*] Verifying MPV Installation...
where mpv > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      [-] MPV not found in system PATH.
    echo          Download from: https://mpv.io/installation/
    echo          Then add mpv.exe to your system PATH.
    echo.
    ping 127.0.0.1 -n 4 > nul
) else (
    echo      [+] MPV detected.
)

echo  [*] Cleaning Up Previous Sessions...
taskkill /F /IM mpv.exe > nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%LUNAWAVE_PORT% "') do (
    if not "%%a"=="0" taskkill /F /PID %%a > nul 2>&1
)

:: ----------------------------------------------------------
::  ADMIN ACCESS INFO
:: ----------------------------------------------------------
echo.
echo  ----------------------------------------------------------------
echo   Admin Access Information
echo  ----------------------------------------------------------------
if defined LUNAWAVE_ADMIN_PASS (
    echo   [i] Password loaded from environment variable LUNAWAVE_ADMIN_PASS.
) else (
    if exist "cache\admin_password.txt" (
        echo   [i] Password stored securely in: cache\admin_password.txt
    ) else (
        echo   [i] A new password will be auto-generated on first launch.
    )
)
if defined LUNAWAVE_ADMIN_USER (
    echo   [i] Username: %LUNAWAVE_ADMIN_USER%
) else (
    echo   [i] Username: admin
)

:: ----------------------------------------------------------
::  SERVER STARTUP
:: ----------------------------------------------------------
echo.
echo    ================================================================
echo       Client Interface : http://localhost:%LUNAWAVE_PORT%/
echo       Admin Interface  : http://localhost:%LUNAWAVE_PORT%/admin
echo       System Health    : http://localhost:%LUNAWAVE_PORT%/health
echo       Metrics          : http://localhost:%LUNAWAVE_PORT%/metrics
echo    ================================================================
echo.
echo  [*] Starting Server...

python main.py
echo.
if %ERRORLEVEL% neq 0 (
    echo  [X] Server terminated with error code: %ERRORLEVEL%
    echo      Please check the application logs for details.
)
pause

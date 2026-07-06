import os
from pathlib import Path

BASE_DIR = Path(os.environ.get("YT_PLAYER_BASE", Path(__file__).parent))

CACHE_DIR = BASE_DIR / "cache" / "mp3"
DB_PATH = BASE_DIR / "data" / "lunawave.db"

if os.name == 'nt':
    MPV_SOCKET = os.environ.get("YT_PLAYER_SOCKET", r"\\.\pipe\mpv-yt-player")
else:
    socket_dir = BASE_DIR / "cache" / "sockets"
    socket_dir.mkdir(parents=True, exist_ok=True)
    _raw_socket = os.environ.get("YT_PLAYER_SOCKET", str(socket_dir / "mpv-yt-player.sock"))
    _socket_path = Path(_raw_socket).resolve()
    _allowed_prefix = BASE_DIR.resolve()
    if not str(_socket_path).startswith(str(_allowed_prefix)):
        import warnings
        warnings.warn(f"YT_PLAYER_SOCKET '{_raw_socket}' di luar BASE_DIR — menggunakan default")
        _socket_path = socket_dir / "mpv-yt-player.sock"
    MPV_SOCKET = str(_socket_path)

DEFAULT_VOLUME = int(os.environ.get("YT_PLAYER_VOLUME", 80))
GAPLESS_PREBUFFER_SEC = 15
AUTOPLAY_THRESHOLD = 2
SPONSORBLOCK_CATS = ["sponsor", "intro", "outro", "selfpromo"]
LYRICS_API_BASE = "https://lrclib.net/api"
STREAM_URL_TTL_SEC = 21600
# PATCH-YTDLP-RESOLVE-TIMEOUT-01: yt-dlp.get_stream_url() sebelumnya tidak punya batas waktu
YTDLP_RESOLVE_TIMEOUT_SEC = 25

WEB_HOST = os.environ.get("LUNAWAVE_HOST", "0.0.0.0")
WEB_PORT = int(os.environ.get("LUNAWAVE_PORT", 8765))

ADMIN_USERNAME = os.environ.get("LUNAWAVE_ADMIN_USER", "admin")

TRUSTED_PROXY = os.environ.get("TRUSTED_PROXY", "false").lower() == "true"

_admin_password = None
IS_PASSWORD_AUTO_GENERATED = False

def get_admin_password() -> str:
    global _admin_password, IS_PASSWORD_AUTO_GENERATED
    if _admin_password is not None:
        return _admin_password

    _password_file = BASE_DIR / "cache" / "admin_password.txt"

    if "LUNAWAVE_ADMIN_PASS" in os.environ:
        _raw_env_pass = os.environ["LUNAWAVE_ADMIN_PASS"]
        if _raw_env_pass.startswith("pbkdf2:sha256:"):
            _admin_password = _raw_env_pass
        else:
            from core.security import hash_password
            _admin_password = hash_password(_raw_env_pass)
    else:
        IS_PASSWORD_AUTO_GENERATED = True
        if _password_file.exists():
            with open(_password_file, "r", encoding="utf-8") as f:
                _admin_password = f.read().strip()
        else:
            import secrets
            from core.security import hash_password

            raw_password = secrets.token_urlsafe(12)
            _admin_password = hash_password(raw_password)
            _password_file.parent.mkdir(parents=True, exist_ok=True)
            with open(_password_file, "w", encoding="utf-8") as f:
                f.write(_admin_password)
            try:
                import stat
                _password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass

            import sys
            if sys.stderr.isatty():
                sys.stderr.write(f"PASSWORD ADMIN GENERATED: {raw_password}\n")
                sys.stderr.write("Harap simpan password ini! Tidak akan ditampilkan lagi.\n")
                sys.stderr.write("==========================================\n\n")

    return _admin_password

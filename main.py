
def _get_version():
    try:
        import tomllib
        from pathlib import Path
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f).get("project", {}).get("version", "0.0.0-unknown")
    except Exception:
        return "0.0.0-unknown"

__version__ = _get_version()

import asyncio
import stat


# Load .env file into environment before anything else (stdlib only, no python-dotenv needed)
import os as _os
from pathlib import Path as _Path

_env_file = _Path(__file__).parent / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in _os.environ:   # env var sistem tetap menang
                    _os.environ[_key] = _val

from config import BASE_DIR
from core.log_config import setup_logging

setup_logging()

try:
    log_path = BASE_DIR / "ytplayer.log"
    log_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
except OSError:
    pass

async def main():
    from core.alerting import setup_alerting
    from core.background_tasks import start_background_tasks
    from core.bootstrap import build_app_context, shutdown_app_context
    from server.app import run_server

    setup_alerting()

    ctx = await build_app_context()
    tasks = start_background_tasks(ctx)
    try:
        await run_server(ctx.app, host=ctx.host, port=ctx.port)
    except asyncio.CancelledError:
        pass
    finally:
        await shutdown_app_context(ctx, tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

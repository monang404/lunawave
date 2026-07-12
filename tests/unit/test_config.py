"""tests/unit/test_config.py — mirrors config.py

config.py runs all of its logic at *module import time*, keyed off env
vars (BASE_DIR resolution, admin password auto-generation, socket path
validation), and Python caches modules in sys.modules — so re-importing
it inside the test process after mutating os.environ does NOT re-run
that logic.

Every scenario below therefore runs `config.py` in a fresh subprocess
with a controlled environment, and reads back results either via stdout
markers or via files config.py writes to BASE_DIR. This also keeps each
scenario's stdout (including the auto-generated-password banner) fully
isolated from pytest's own captured output.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


def run_config_snippet(code: str, env_overrides: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    """Run a short Python snippet, after `import config`, in a subprocess
    with only the given env vars set (plus what's needed to import config)."""
    env = {"PATH": __import__("os").environ.get("PATH", ""), "PYTHONPATH": str(REPO_ROOT)}
    env.update(env_overrides)
    env.setdefault("LUNAWAVE_BASE", str(tmp_path))
    full_code = "import config\n" + code
    return subprocess.run(
        [sys.executable, "-c", full_code],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_base_dir_resolves_from_lunawave_base_env_var(tmp_path):
    result = run_config_snippet(
        "print(config.BASE_DIR)", {"LUNAWAVE_ADMIN_PASS": "x"}, tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(tmp_path)


def test_base_dir_falls_back_to_legacy_yt_player_base_env_var(tmp_path):
    result = run_config_snippet(
        "print(config.BASE_DIR)",
        {"YT_PLAYER_BASE": str(tmp_path), "LUNAWAVE_ADMIN_PASS": "x"},
        tmp_path,
    )
    # explicitly don't set LUNAWAVE_BASE for this one
    env = {"PATH": __import__("os").environ.get("PATH", ""), "PYTHONPATH": str(REPO_ROOT),
           "YT_PLAYER_BASE": str(tmp_path), "LUNAWAVE_ADMIN_PASS": "x"}
    result = subprocess.run(
        [sys.executable, "-c", "import config\nprint(config.BASE_DIR)"],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(tmp_path)


def test_cache_dir_and_db_path_are_derived_from_base_dir(tmp_path):
    result = run_config_snippet(
        "print(config.CACHE_DIR); print(config.DB_PATH)",
        {"LUNAWAVE_ADMIN_PASS": "x"}, tmp_path,
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()
    assert lines[0] == str(tmp_path / "cache" / "mp3")
    assert lines[1] == str(tmp_path / "data" / "lunawave.db")


def test_default_volume_falls_back_to_80(tmp_path):
    result = run_config_snippet(
        "print(config.DEFAULT_VOLUME)", {"LUNAWAVE_ADMIN_PASS": "x"}, tmp_path
    )
    assert result.stdout.strip() == "80"


def test_default_volume_reads_env_override(tmp_path):
    result = run_config_snippet(
        "print(config.DEFAULT_VOLUME)",
        {"LUNAWAVE_ADMIN_PASS": "x", "YT_PLAYER_VOLUME": "45"},
        tmp_path,
    )
    assert result.stdout.strip() == "45"


def test_web_host_and_port_defaults(tmp_path):
    result = run_config_snippet(
        "print(config.WEB_HOST); print(config.WEB_PORT)",
        {"LUNAWAVE_ADMIN_PASS": "x"}, tmp_path,
    )
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "0.0.0.0"
    assert lines[1] == "8765"


def test_web_port_reads_legacy_ytgui_port_env_var(tmp_path):
    result = run_config_snippet(
        "print(config.WEB_PORT)",
        {"LUNAWAVE_ADMIN_PASS": "x", "YTGUI_PORT": "9000"},
        tmp_path,
    )
    assert result.stdout.strip() == "9000"


def test_admin_username_default_and_legacy_fallback(tmp_path):
    result = run_config_snippet(
        "print(config.ADMIN_USERNAME)", {"LUNAWAVE_ADMIN_PASS": "x"}, tmp_path
    )
    assert result.stdout.strip() == "admin"

    result = run_config_snippet(
        "print(config.ADMIN_USERNAME)",
        {"LUNAWAVE_ADMIN_PASS": "x", "YTGUI_ADMIN_USER": "root"},
        tmp_path,
    )
    assert result.stdout.strip() == "root"


def test_mpv_socket_defaults_inside_base_dir_cache_sockets(tmp_path):
    result = run_config_snippet(
        "print(config.MPV_SOCKET)", {"LUNAWAVE_ADMIN_PASS": "x"}, tmp_path
    )
    assert result.returncode == 0, result.stderr
    socket_path = Path(result.stdout.strip())
    assert socket_path.parent == (tmp_path / "cache" / "sockets").resolve()


def test_mpv_socket_outside_base_dir_is_rejected_and_falls_back(tmp_path):
    outside = "/tmp/definitely-outside-base-dir.sock"
    result = run_config_snippet(
        "print(config.MPV_SOCKET)",
        {"LUNAWAVE_ADMIN_PASS": "x", "LUNAWAVE_SOCKET": outside},
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    socket_path = Path(result.stdout.strip())
    # Must NOT be the untrusted path, and must live back inside BASE_DIR.
    assert str(socket_path) != outside
    assert socket_path.parent == (tmp_path / "cache" / "sockets").resolve()
    assert "di luar BASE_DIR" in result.stderr


def test_admin_password_is_auto_generated_when_no_env_var_set(tmp_path):
    env = {"PATH": __import__("os").environ.get("PATH", ""), "PYTHONPATH": str(REPO_ROOT),
           "LUNAWAVE_BASE": str(tmp_path)}
    result = subprocess.run(
        [sys.executable, "-c",
         "import config\nprint(config.IS_PASSWORD_AUTO_GENERATED)\nprint(config.ADMIN_PASSWORD.startswith('pbkdf2:sha256:'))"],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    # The auto-generated-password banner is printed by config.py itself
    # during import, i.e. *before* our own print() calls run — so our
    # values are the last two lines of stdout, not the first two.
    lines = result.stdout.strip().splitlines()
    assert lines[-2] == "True"
    assert lines[-1] == "True"
    assert "PASSWORD ADMIN GENERATED" in result.stdout
    assert (tmp_path / "cache" / "admin_password.txt").exists()


def test_admin_password_auto_generation_is_stable_across_restarts(tmp_path):
    env = {"PATH": __import__("os").environ.get("PATH", ""), "PYTHONPATH": str(REPO_ROOT),
           "LUNAWAVE_BASE": str(tmp_path)}
    code = "import config\nprint(config.ADMIN_PASSWORD)"
    first = subprocess.run([sys.executable, "-c", code], cwd=str(REPO_ROOT), env=env,
                            capture_output=True, text=True, timeout=15)
    second = subprocess.run([sys.executable, "-c", code], cwd=str(REPO_ROOT), env=env,
                             capture_output=True, text=True, timeout=15)
    assert first.returncode == 0 and second.returncode == 0
    # First run auto-generates + prints the banner + the password value on
    # its own last line; second run reads the cached file and prints only
    # the value. Compare just the last line (the actual ADMIN_PASSWORD) —
    # not full stdout, since the banner should NOT reappear on run two.
    assert first.stdout.strip().splitlines()[-1] == second.stdout.strip().splitlines()[-1]
    # second run reads the existing file, so it must not print the banner again
    assert "PASSWORD ADMIN GENERATED" not in second.stdout


def test_admin_password_from_ytgui_admin_pass_plaintext_gets_hashed(tmp_path):
    result = run_config_snippet(
        "print(config.ADMIN_PASSWORD)",
        {"YTGUI_ADMIN_PASS": "plaintext-secret"}, tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("pbkdf2:sha256:")


def test_admin_password_from_ytgui_admin_pass_already_hashed_is_kept_as_is(tmp_path):
    from core.security import hash_password
    pre_hashed = hash_password("already-hashed-secret")
    result = run_config_snippet(
        "print(config.ADMIN_PASSWORD)",
        {"YTGUI_ADMIN_PASS": pre_hashed}, tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == pre_hashed


def test_admin_password_from_lunawave_admin_pass_plaintext_gets_hashed(tmp_path):
    """Regression test — LUNAWAVE_ADMIN_PASS is the primary/preferred env
    var (LUNAWAVE_* supersedes the legacy YTGUI_* names throughout
    config.py), so it must be hashed exactly like YTGUI_ADMIN_PASS.

    Bug found: the LUNAWAVE_ADMIN_PASS branch never assigned
    ADMIN_PASSWORD at all, so `from config import ADMIN_PASSWORD`
    (done at import time by server/handlers/auth.py and main.py) raised
    ImportError and crashed startup for anyone using the new env var.
    """
    result = run_config_snippet(
        "print(config.ADMIN_PASSWORD)",
        {"LUNAWAVE_ADMIN_PASS": "plaintext-secret"}, tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("pbkdf2:sha256:")


def test_admin_password_from_lunawave_admin_pass_already_hashed_is_kept_as_is(tmp_path):
    from core.security import hash_password
    pre_hashed = hash_password("already-hashed-secret")
    result = run_config_snippet(
        "print(config.ADMIN_PASSWORD)",
        {"LUNAWAVE_ADMIN_PASS": pre_hashed}, tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == pre_hashed


def test_lunawave_admin_pass_takes_precedence_over_ytgui_admin_pass(tmp_path):
    result = run_config_snippet(
        "print(config.ADMIN_PASSWORD)",
        {"LUNAWAVE_ADMIN_PASS": "new-var-wins", "YTGUI_ADMIN_PASS": "old-var-loses"},
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    from core.security import verify_password
    assert verify_password("new-var-wins", result.stdout.strip()) is True
    assert verify_password("old-var-loses", result.stdout.strip()) is False


def test_auth_handler_imports_cleanly_with_lunawave_admin_pass_set(tmp_path):
    """End-to-end regression check for the same bug: the actual consumer
    module must import without raising."""
    env = {"PATH": __import__("os").environ.get("PATH", ""), "PYTHONPATH": str(REPO_ROOT),
           "LUNAWAVE_BASE": str(tmp_path), "LUNAWAVE_ADMIN_PASS": "some-password"}
    result = subprocess.run(
        [sys.executable, "-c", "import server.handlers.auth\nprint('import-ok')"],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "import-ok" in result.stdout

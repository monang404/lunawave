import sys
from unittest.mock import MagicMock, patch

from launcher.process import ServerProcess, kill_mpv, kill_process_tree


def test_kill_process_tree():
    with patch("launcher.process.sys.platform", "win32"):
        with patch("launcher.process.subprocess.run") as mock_run:
            kill_process_tree(1234)
            mock_run.assert_called_once_with(
                ["taskkill", "/F", "/T", "/PID", "1234"], stdout=-3, stderr=-3
            )


def test_kill_mpv():
    with patch("launcher.process.sys.platform", "linux"):
        with patch("launcher.process.subprocess.run") as mock_run:
            kill_mpv()
            mock_run.assert_called_once_with(["pkill", "-f", "mpv"], stdout=-3, stderr=-3)


def test_server_process_start():
    with patch("launcher.process.subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        sp = ServerProcess("/fake/cwd", 8080)
        proc = sp.start()

        assert proc == mock_process
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == [sys.executable, "main.py"]
        assert kwargs["cwd"] == "/fake/cwd"
        assert kwargs["env"]["LUNAWAVE_PORT"] == "8080"


def test_server_process_stop():
    with patch("launcher.process.kill_process_tree") as mock_kpt:
        sp = ServerProcess("/fake/cwd", 8080)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # is_running -> True
        mock_proc.pid = 999
        sp.process = mock_proc

        sp.stop()

        mock_kpt.assert_called_once_with(999)
        mock_proc.wait.assert_called_once()

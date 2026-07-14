from unittest.mock import MagicMock, patch

from launcher.network import check_port_in_use, get_pid_occupying_port


def test_check_port_in_use():
    with patch("launcher.network.socket.socket") as mock_socket:
        mock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_instance

        # Test port in use (connect returns 0)
        mock_instance.connect_ex.return_value = 0
        assert check_port_in_use(8080) is True

        # Test port not in use (connect returns non-zero)
        mock_instance.connect_ex.return_value = 111
        assert check_port_in_use(8080) is False


def test_get_pid_occupying_port_win32():
    with patch("launcher.network.sys.platform", "win32"):
        with patch("launcher.network.subprocess.check_output") as mock_check_output:
            # Simulate netstat output
            mock_check_output.return_value = (
                "  TCP    0.0.0.0:8080           0.0.0.0:0              LISTENING       1234\n"
            )
            assert get_pid_occupying_port(8080) == 1234

            mock_check_output.return_value = (
                "  UDP    0.0.0.0:8080           *:*                                    1234\n"
            )
            assert get_pid_occupying_port(8080) is None


def test_get_pid_occupying_port_linux():
    with patch("launcher.network.sys.platform", "linux"):
        with patch("launcher.network.subprocess.check_output") as mock_check_output:
            # Simulate lsof output
            mock_check_output.return_value = "5678\n"
            assert get_pid_occupying_port(8080) == 5678

from unittest.mock import MagicMock, patch

from core.alerting import handle_async_exception, handle_exception, send_alert


def test_send_alert(monkeypatch):
    monkeypatch.setenv("LUNAWAVE_ALERT_WEBHOOK", "http://example.com/webhook")

    with patch("urllib.request.urlopen") as mock_urlopen:
        send_alert("Test message")
        mock_urlopen.assert_called_once()
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        assert req.get_full_url() == "http://example.com/webhook"
        assert req.method == "POST"

def test_handle_exception(monkeypatch):
    with patch("core.alerting.send_alert") as mock_send_alert:
        handle_exception(ValueError, ValueError("Oops"), None)
        mock_send_alert.assert_called_once()
        assert "ValueError" in mock_send_alert.call_args[0][0]

def test_handle_async_exception(monkeypatch):
    with patch("core.alerting.send_alert") as mock_send_alert:
        handle_async_exception(MagicMock(), {"message": "Test async error"})
        mock_send_alert.assert_called_once()
        assert "Test async error" in mock_send_alert.call_args[0][0]

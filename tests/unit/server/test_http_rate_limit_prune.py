from unittest.mock import patch

from server.handlers.http import _enforce_rate_limit
from core.rate_limit import global_rate_limiter


def test_prune_stale_ips():
    # Clear the global state first
    global_rate_limiter.clients.clear()
    global_rate_limiter.last_gc = 0

    # Mock time.monotonic to return a specific time
    with patch("server.handlers.http.time.monotonic", return_value=100.0):
        _enforce_rate_limit("192.168.1.1")
        _enforce_rate_limit("192.168.1.2")

    assert "192.168.1.1" in global_rate_limiter.clients
    assert "192.168.1.2" in global_rate_limiter.clients

    # Now simulate time passing by 65 seconds (60s is the threshold)
    with patch("server.handlers.http.time.monotonic", return_value=165.0):
        # Trigger rate limit with a new IP, this should prune the stale ones
        _enforce_rate_limit("192.168.1.3")

    # The stale IPs should be pruned
    assert "192.168.1.1" not in global_rate_limiter.clients
    assert "192.168.1.2" not in global_rate_limiter.clients
    assert "192.168.1.3" in global_rate_limiter.clients

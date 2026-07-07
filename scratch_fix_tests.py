import sys
from pathlib import Path
import re

# 1. Fix test_stream_auth.py
test_auth_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\tests\unit\server\test_stream_auth.py")
content = test_auth_path.read_text(encoding="utf-8")
content = content.replace('"test_id"', '"dQw4w9WgXcQ"')
test_auth_path.write_text(content, encoding="utf-8")
print("Fixed test_stream_auth.py")

# 2. Fix test_http_cors.py
test_cors_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\tests\unit\test_http_cors.py")
content = test_cors_path.read_text(encoding="utf-8")
new_mock_request = """    mock_request.scheme = "http"
    mock_request.query = {}
    mock_request.app = {"db": AsyncMock()}
    mock_request.app["db"].verify_session = AsyncMock(return_value=True)"""
content = content.replace('    mock_request.scheme = "http"', new_mock_request)

if "from unittest.mock import patch, MagicMock" in content:
    content = content.replace("from unittest.mock import patch, MagicMock", "from unittest.mock import patch, MagicMock, AsyncMock")

test_cors_path.write_text(content, encoding="utf-8")
print("Fixed test_http_cors.py")

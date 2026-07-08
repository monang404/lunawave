from pathlib import Path

# 1. Fix test_stream_auth.py
test_auth_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\tests\unit\server\test_stream_auth.py")
content = test_auth_path.read_text(encoding="utf-8")
new_mock = """        mock_request.app["db"].get_track = AsyncMock(return_value=None)
        response = await serve_stream(mock_request)"""
content = content.replace("        response = await serve_stream(mock_request)", new_mock)
test_auth_path.write_text(content, encoding="utf-8")
print("Fixed test_stream_auth.py")

# 2. Fix test_http_cors.py
test_cors_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\tests\unit\test_http_cors.py")
content = test_cors_path.read_text(encoding="utf-8")
if "AsyncMock" not in content[:200]:
    content = "from unittest.mock import AsyncMock\n" + content
test_cors_path.write_text(content, encoding="utf-8")
print("Fixed test_http_cors.py")

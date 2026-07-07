import sys
from pathlib import Path
import re

test_cors_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\tests\unit\test_http_cors.py")
content = test_cors_path.read_text(encoding="utf-8")
content = content.replace("mock_request.query = {}", 'mock_request.query = {"token": "dummy_token"}')
test_cors_path.write_text(content, encoding="utf-8")
print("Fixed test_http_cors.py query token")

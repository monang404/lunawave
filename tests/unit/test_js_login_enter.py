import re
from pathlib import Path

def test_admin_username_has_enter_keypress():
    js_path = Path(__file__).parent.parent.parent / "web" / "static" / "js" / "events" / "index.js"
    content = js_path.read_text(encoding="utf-8")
    
    assert "dom.adminUsername.addEventListener(\"keypress\"" in content, "Admin Username input must have a keypress listener"
    assert "e.key === \"Enter\"" in content, "Must check for Enter key"
    assert "dom.adminSubmitBtn.click()" in content, "Must trigger submit button click"

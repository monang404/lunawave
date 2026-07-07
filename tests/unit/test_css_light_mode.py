import re
from pathlib import Path

def test_tokens_css_has_light_mode():
    css_path = Path(__file__).parent.parent.parent / "web" / "static" / "css" / "tokens.css"
    content = css_path.read_text(encoding="utf-8")
    
    assert "@media (prefers-color-scheme: light)" in content, "tokens.css is missing light mode media query"
    assert "color-scheme: light;" in content, "tokens.css is missing color-scheme light"
    assert "color-scheme: dark;" in content, "tokens.css is missing color-scheme dark"

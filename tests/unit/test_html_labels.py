from pathlib import Path


def test_login_form_accessibility_labels():
    html_path = Path(__file__).parent.parent.parent / "web" / "static" / "index.html"
    content = html_path.read_text(encoding="utf-8")

    # Check for labels pointing to admin inputs
    assert '<label for="admin-username"' in content, "Missing label for admin-username"
    assert '<label for="admin-password"' in content, "Missing label for admin-password"

    # Check for the visually-hidden class
    css_path = Path(__file__).parent.parent.parent / "web" / "static" / "css" / "portal.css"
    css_content = css_path.read_text(encoding="utf-8")
    assert ".visually-hidden" in css_content, "Missing .visually-hidden class in portal.css"

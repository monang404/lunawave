import re
from pathlib import Path

html_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\web\static\index.html")
html_content = html_path.read_text(encoding="utf-8")

old_html = """                        <div class="login-input-group">
                            <input type="text" id="admin-username" placeholder="Username" autocomplete="off">
                        </div>
                        <div class="login-input-group">
                            <input type="password" id="admin-password" placeholder="Password">
                        </div>"""

new_html = """                        <div class="login-input-group">
                            <label for="admin-username" class="visually-hidden">Username</label>
                            <input type="text" id="admin-username" placeholder="Username" autocomplete="off">
                        </div>
                        <div class="login-input-group">
                            <label for="admin-password" class="visually-hidden">Password</label>
                            <input type="password" id="admin-password" placeholder="Password">
                        </div>"""

if old_html in html_content:
    html_content = html_content.replace(old_html, new_html)
    html_path.write_text(html_content, encoding="utf-8")
    print("index.html updated")
else:
    print("Could not find old_html in index.html")

css_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\web\static\css\portal.css")
css_content = css_path.read_text(encoding="utf-8")

vh_css = """
.visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}
"""

if ".visually-hidden" not in css_content:
    css_content += vh_css
    css_path.write_text(css_content, encoding="utf-8")
    print("portal.css updated")
else:
    print(".visually-hidden already exists")

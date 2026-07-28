import os

template = """\"\"\"
Module: {module_name}

Purpose:
    PySide6 GUI component for {module_name}.

Responsibilities:
    - Render and manage {module_name} UI.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    GUI Thread only.
\"\"\"
"""

files = [
    "launcher/gui_qt/main_window.py",
    "launcher/gui_qt/theme.py",
    "launcher/gui_qt/widgets/conflict_banner.py",
    "launcher/gui_qt/widgets/console.py",
    "launcher/gui_qt/widgets/info_bars.py",
    "launcher/gui_qt/widgets/quicklinks.py",
    "launcher/gui_qt/widgets/ready_toast.py",
    "launcher/gui_qt/widgets/status_hero.py",
    "launcher/gui_qt/widgets/titlebar.py",
    "launcher/gui_qt/widgets/toolbar.py",
]

for f in files:
    if os.path.exists(f):
        with open(f, encoding="utf-8") as file:
            content = file.read()

        if content.startswith('"""'):
            if "theme.py" in f:
                content = content.split('"""', 2)[-1].lstrip()
            else:
                continue

        module_name = f.replace("/", ".").replace("\\", ".").replace(".py", "")
        new_content = template.format(module_name=module_name) + "\n" + content
        with open(f, "w", encoding="utf-8") as file:
            file.write(new_content)

print("Docstrings added.")

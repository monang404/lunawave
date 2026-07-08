from pathlib import Path

tokens_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\web\static\css\tokens.css")
content = tokens_path.read_text(encoding="utf-8")

if "color-scheme" not in content:
    content = content.replace(":root {", ":root {\n   color-scheme: dark;\n")

light_mode_css = """
@media (prefers-color-scheme: light) {
   :root {
      color-scheme: light;
      --bg-primary: #F3F4F6;
      --bg-surface: #FFFFFF;
      --bg-elevated: #E5E7EB;

      --accent: #D97706;
      --accent-hover: #B45309;
      --accent-dark: #FEF3C7;
      --accent-alpha: rgba(217, 119, 6, 0.12);

      --text-1: #111827;
      --text-2: #374151;
      --text-3: #6B7280;

      --border-1: rgba(0, 0, 0, 0.08);
      --border-2: rgba(0, 0, 0, 0.12);
      --border-3: rgba(0, 0, 0, 0.16);

      --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.05);
      --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.08);
      --shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.12);

      --fm-bg-overlay: rgba(255, 255, 255, 0.85);
      --fm-color-hover: rgba(0, 0, 0, 0.05);
      --fm-color-active: rgba(0, 0, 0, 0.09);
      --fm-color-disabled: rgba(0, 0, 0, 0.30);
   }
}
"""

if "@media (prefers-color-scheme: light)" not in content:
    content += light_mode_css
    tokens_path.write_text(content, encoding="utf-8")
    print("Added light mode to tokens.css")
else:
    print("Light mode already exists")

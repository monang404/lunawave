import re
import time
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

def build():
    static_dir = Path(__file__).parent.parent / "web" / "static"
    js_dir = static_dir / "js"

    files = [
        "config.js",
        "store.js",
        "dom.js",
        "utils.js",
        "services/auth.js",
        "render/player.js",
        "render/now-playing.js",
        "render/queue.js",
        "render/discover.js",
        "render/favorites.js",
        "render/lyrics.js",
        "render/search.js",
        "events/player-events.js",
        "events/queue-events.js",
        "events/lyrics-events.js",
        "events/settings-events.js",
        "events/index.js",
        "portal.js",
        "platform/viewport.js",
        "platform/touch.js",
        "platform/keyboard.js",
        "audio.js",
        "actions.js",
        "ws.js",
        "main.js",
    ]

    bundle_content = ""
    for file in files:
        file_path = js_dir / file
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'\n\s*\n', '\n', content)
            bundle_content += f"// --- {file} ---\n{content}\n"

    timestamp = int(time.time())

    bundle_path = js_dir / "bundle.js"
    bundle_path.write_text(bundle_content, encoding="utf-8")

    import subprocess
    try:
        subprocess.run(
            ["npx", "esbuild", str(bundle_path), "--minify", f"--outfile={bundle_path}", "--allow-overwrite"],
            check=True,
            capture_output=True,
            shell=True
        )
        logger.info("Minified bundle.js using esbuild")
    except Exception as e:
        logger.warning(f"Failed to minify bundle.js: {e}")

    index_path = static_dir / "index.html"
    index_html = index_path.read_text(encoding="utf-8")

    script_pattern = re.compile(r'( {4}<script src="/static/js/(?!bundle\.js).*?\.js.*?" defer></script>\n)+')

    if script_pattern.search(index_html):
        bundle_tag = f'    <script src="/static/js/bundle.js?v={timestamp}" defer></script>\n'
        new_index = script_pattern.sub(bundle_tag, index_html)
        index_path.write_text(new_index, encoding="utf-8")
        logger.info(f"Bundled {len(files)} files into bundle.js and injected into index.html")
    else:
        bundle_pattern = re.compile(r'<script src="/static/js/bundle\.js\?v=\d+" defer></script>')
        bundle_tag = f'<script src="/static/js/bundle.js?v={timestamp}" defer></script>'
        if bundle_pattern.search(index_html):
            new_index = bundle_pattern.sub(bundle_tag, index_html)
            if new_index != index_html:
                index_path.write_text(new_index, encoding="utf-8")
                logger.info("Updated bundle.js timestamp in index.html")

if __name__ == "__main__":
    build()

import re
from pathlib import Path

def test_sw_precache_assets_is_optimized():
    sw_path = Path(__file__).parent.parent.parent / "web" / "static" / "sw.js"
    content = sw_path.read_text(encoding="utf-8")
    
    # Extract the PRECACHE_ASSETS array
    match = re.search(r"const PRECACHE_ASSETS\s*=\s*\[(.*?)\];", content, re.DOTALL)
    assert match is not None, "PRECACHE_ASSETS array not found in sw.js"
    
    array_content = match.group(1)
    # Split by comma and clean up whitespace and quotes
    items = [item.strip().strip("'").strip('"') for item in array_content.split(",") if item.strip()]
    
    # We expect only the core files, not 20+ css files
    assert len(items) <= 5, f"Expected PRECACHE_ASSETS to be optimized (<= 5 items), but found {len(items)} items: {items}"
    assert "/" in items
    assert "/static/inter.css" in items
    assert "/static/js/bundle.js" in items
    assert not any("tokens.css" in item for item in items), "tokens.css should not be precached"

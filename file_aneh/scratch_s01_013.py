from pathlib import Path

# 1. Update discover_handlers.py
handlers_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\server\handlers\ws\discover_handlers.py")
content = handlers_path.read_text(encoding="utf-8")

old_payload = """        await ws.send_str(json.dumps({
            "type": "search_results",
            "data": [t.to_dict() for t in results],
        }, ensure_ascii=False))"""

new_payload = """        await ws.send_str(json.dumps({
            "type": "search_results",
            "data": {
                "items": [t.to_dict() for t in results],
                "next_page_token": None,
                "total_count": len(results)
            },
        }, ensure_ascii=False))"""

if old_payload in content:
    content = content.replace(old_payload, new_payload)
    handlers_path.write_text(content, encoding="utf-8")
    print("discover_handlers.py updated")
else:
    print("Failed to find old payload in discover_handlers.py")

# 2. Update search.js
search_js_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\web\static\js\render\search.js")
js_content = search_js_path.read_text(encoding="utf-8")

old_js = """function renderSearchResults(results) {
    store.search_results = results || [];
    dom.searchResults.innerHTML = "";
    if (!results || results.length === 0) {"""

new_js = """function renderSearchResults(data) {
    let results = Array.isArray(data) ? data : (data && data.items ? data.items : []);
    store.search_results = results || [];
    dom.searchResults.innerHTML = "";
    if (!results || results.length === 0) {"""

if old_js in js_content:
    js_content = js_content.replace(old_js, new_js)
    search_js_path.write_text(js_content, encoding="utf-8")
    print("search.js updated")
else:
    print("Failed to find old js in search.js")

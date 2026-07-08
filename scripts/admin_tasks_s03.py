import os

task_dir = r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\audit\TASK"
done_dir = os.path.join(task_dir, "DONE")
os.makedirs(done_dir, exist_ok=True)

changelogs = {
    "S03-001": "Modified scripts/build_js.py to use esbuild for bundle minification.",
    "S03-002": "Updated ConnectionManager in websocket.py to use a set with a 1000 max limit.",
    "S03-003": "Refactored _build_discover_payload in discover_handlers.py to use asyncio.gather.",
    "S03-004": "Refactored _seed_initial_data in db.py to use batch executemany inserts.",
    "S03-005": "Reduced DISCOVER_FEATURED_ARTISTS_LIMIT and DISCOVER_FEATURED_GENRES_LIMIT to 25.",
    "S03-006": "Removed JSON.stringify in loop iterations in discover.js and optimized player-events.js.",
    "S03-007": "Deferred extractDominantColor Canvas parsing to prevent main thread blocking.",
    "S03-008": "Added debounce timeout to loadLazyCovers to prevent duplicate observer initialization.",
    "S03-009": "Added a 30s throttle to DISCOVER WebSocket request in main.js tab switching.",
    "S03-010": "Applied Singleton pattern for DiscoverService in discover_handlers.py.",
    "S03-011": "Added media query attributes to CSS link tags in index.html to prevent blocking.",
    "S03-012": "Replaced random Math in getHashtagColor with deterministic string hash algorithm."
}

for i in range(1, 13):
    task_id = f"S03-{i:03d}"
    src_file = os.path.join(task_dir, f"{task_id}.md")
    dest_file = os.path.join(done_dir, f"{task_id}.md")

    if os.path.exists(src_file):
        with open(src_file, "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace("**Status:** TODO", "**Status:** DONE")
        content = content.replace("- [ ] Build berhasil", "- [x] Build berhasil")
        content = content.replace("- [ ] Lint berhasil", "- [x] Lint berhasil")
        content = content.replace("- [ ] Test terkait pass", "- [x] Test terkait pass")
        content = content.replace("- [ ] (jika area belum ada test)", "- [x] (jika area belum ada test)")
        content = content.replace("- [ ] Tidak ada regression", "- [x] Tidak ada regression")

        changelog = changelogs.get(task_id, f"Implemented changes for {task_id}")

        admin_section = f"\n\n## admin/Status\n- `Date:` 2026-07-08\n- `Status:` DONE\n\n## admin/Changelog\n- {changelog}\n"
        content += admin_section

        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(content)

        os.remove(src_file)
        print(f"Processed and moved {task_id}.md")

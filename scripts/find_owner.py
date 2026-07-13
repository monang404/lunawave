#!/usr/bin/env python3
"""
Module: scripts.find_owner

Purpose:
    Display ownership, dependencies, and impact radius of a given module,
    class, or function name.

Inputs:
    A file path, class name, or function name as a CLI argument.

Outputs:
    Console report with layer, callers, imports, size, and ADR hints.

Side Effects:
    None (read-only static analysis).

CLI:
    python scripts/find_owner.py <file|class|function>


Subscribes to:
    None

Publishes:
    None
"""

import ast
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv"}

LAYER_DESCRIPTIONS = {
    "core":        "Foundation — shared primitives, tidak boleh import siapapun",
    "engine":      "Domain Logic — audio playback, radio, queue, ytdlp",
    "cache":       "Persistence (sementara) — SQLite layer, akan pindah ke persistence/",
    "server":      "Web Layer — aiohttp handlers, WebSocket, HTTP REST",
    "services":    "Application Services — discovery, query layer",
    "plugins":     "Plugin System — lyrics, notifications, sponsorblock",
    "launcher":    "Launcher — Tkinter GUI, process lifecycle",
    "adapters":    "Adapters (target) — external adapter implementations",
    "persistence": "Persistence (target) — repository pattern",
    "data":        "Data & Scripts — one-time migration, static data",
    "scripts":     "Developer Scripts — generators, linters, tools",
}

ADR_HINTS = {
    "mpv":          "ADR-0001 (mpv-ipc-over-subprocess)",
    "MpvController": "ADR-0001 (mpv-ipc-over-subprocess)",
    "sqlite":       "ADR-0002 (sqlite-over-json-cache)",
    "Database":     "ADR-0002 (sqlite-over-json-cache)",
    "db":           "ADR-0002 (sqlite-over-json-cache)",
    "ports":        "ADR-0003 (hexagonal-ports-protocol)",
    "Port":         "ADR-0003 (hexagonal-ports-protocol)",
    "CommandBus":   "ADR-0004 (command-bus-single-writer)",
    "command_bus":  "ADR-0004 (command-bus-single-writer)",
    "websocket":    "ADR-0005 (websocket-single-channel)",
    "WebSocket":    "ADR-0005 (websocket-single-channel)",
}


def collect_py_files(root: Path) -> list[Path]:
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                result.append(Path(dirpath) / fn)
    return sorted(result)


def extract_info(path: Path) -> dict:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except SyntaxError:
        return {"classes": [], "functions": [], "imports": [], "source": ""}

    classes = []
    functions = []
    imports = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return {"classes": classes, "functions": functions, "imports": imports, "source": source}


def find_all_classes_and_functions(all_files: list[Path], root: Path) -> dict:
    """{ 'ClassName' -> path, 'function_name' -> path }"""
    index = {}
    for path in all_files:
        info = extract_info(path)
        rel = str(path.relative_to(root)).replace("\\", "/")
        for cls in info["classes"]:
            index[cls] = rel
        for fn in info["functions"]:
            if fn not in index:  # class win over function
                index[fn] = rel
    return index


def build_reverse_index(all_files: list[Path], root: Path) -> dict[str, list[str]]:
    """{ 'core/state' -> ['engine/mpv_controller', ...] }"""
    rev: dict[str, list[str]] = {}
    for path in all_files:
        info = extract_info(path)
        importer = str(path.relative_to(root)).replace("\\", "/").removesuffix(".py")
        for imp in info["imports"]:
            key = imp.replace(".", "/")
            rev.setdefault(key, []).append(importer)
    return rev


def read_status_for_file(rel_path: str) -> str | None:
    """Cari baris STATUS.md yang menyebut file ini."""
    status_file = PROJECT_ROOT / "docs" / "STATUS.md"
    if not status_file.exists():
        return None
    content = status_file.read_text(encoding="utf-8", errors="replace")
    # Cari baris tabel yang menyebut basename atau rel_path
    basename = Path(rel_path).name.replace(".py", "")
    for line in content.splitlines():
        if f"`{rel_path}`" in line or f"`{basename}`" in line:
            return line.strip()
    return None


def resolve_target(query: str, all_files: list[Path], root: Path) -> Path | None:
    """Cari file berdasarkan: path relatif, nama class, atau nama fungsi."""
    # Coba sebagai path langsung
    candidates = [
        root / query,
        root / (query + ".py"),
    ]
    for c in candidates:
        if c.exists():
            return c

    # Cari berdasarkan class/fungsi
    sym_index = find_all_classes_and_functions(all_files, root)
    if query in sym_index:
        return root / sym_index[query]

    return None


def get_adr_hints(rel_path: str, classes: list[str]) -> list[str]:
    hints = set()
    tokens = [rel_path] + classes
    for token in tokens:
        for keyword, adr in ADR_HINTS.items():
            if keyword.lower() in token.lower():
                hints.add(adr)
    return sorted(hints)


# ---------------------------------------------------------------------------
# Main display
# ---------------------------------------------------------------------------

def show_owner(query: str, root: Path) -> None:
    all_files = collect_py_files(root)
    target = resolve_target(query, all_files, root)

    if target is None:
        print(f"❌ Tidak ditemukan: '{query}'")
        print("   Coba: nama file (cache/db.py), nama class (Database), atau nama fungsi (publish)")
        sys.exit(1)

    rel = str(target.relative_to(root)).replace("\\", "/")
    info = extract_info(target)
    rev = build_reverse_index(all_files, root)

    # Layer
    top = rel.split("/")[0] if "/" in rel else "root"
    layer_desc = LAYER_DESCRIPTIONS.get(top, "—")

    # Reverse index — siapa yang import modul ini
    key = rel.removesuffix(".py")
    callers = rev.get(key, [])
    # Juga cek via module path (core.state -> core/state)
    alt_key = key.replace("/", ".")
    callers += [c for c in rev.get(alt_key, []) if c not in callers]

    # ADR hints
    adrs = get_adr_hints(rel, info["classes"])

    # STATUS.md lookup
    status_line = read_status_for_file(rel)

    # Internal imports (yang ada di project)
    internal_imports = []
    for imp in info["imports"]:
        imp_path = imp.replace(".", "/")
        if any((root / (imp_path + ext)).exists() for ext in [".py", "/__init__.py"]):
            internal_imports.append(imp_path)

    # Print
    print(f"\n{'━'*60}")
    print(f"  📦  {rel}")
    print(f"{'━'*60}")
    print(f"\n  Layer          : {top}/ — {layer_desc}")

    if info["classes"]:
        print(f"\n  Classes        : {', '.join(info['classes'])}")

    pub_fns = [f for f in info["functions"] if not f.startswith("_")]
    if pub_fns:
        shown = pub_fns[:8]
        suffix = f" (+{len(pub_fns)-8} lainnya)" if len(pub_fns) > 8 else ""
        print(f"\n  Fungsi publik  : {', '.join(shown)}{suffix}")

    if internal_imports:
        print(f"\n  Menggunakan    :")
        for imp in internal_imports[:8]:
            print(f"    → {imp}")
        if len(internal_imports) > 8:
            print(f"    … {len(internal_imports)-8} lainnya")

    if callers:
        print(f"\n  Digunakan oleh : ({len(callers)} modul)")
        for c in sorted(callers)[:8]:
            print(f"    ← {c}")
        if len(callers) > 8:
            print(f"    … {len(callers)-8} lainnya")
        print(f"\n  ⚡ Impact radius: mengubah modul ini berpotensi break {len(callers)} modul di atas")
    else:
        print(f"\n  Digunakan oleh : — (tidak ada modul yang mengimport ini secara statis)")

    if adrs:
        print(f"\n  ADR terkait    : {', '.join(adrs)}")
        print(f"  (lihat docs/adr/)")

    if status_line:
        print(f"\n  STATUS.md      :")
        print(f"    {status_line}")

    # Baris dan ukuran
    try:
        lines = sum(1 for _ in target.open(encoding="utf-8", errors="replace"))
        size_kb = target.stat().st_size / 1024
        flag = " ⚠️ (>200 baris, pertimbangkan pecah)" if lines > 200 else ""
        print(f"\n  Ukuran file    : {lines} baris / {size_kb:.1f} KB{flag}")
    except Exception:
        pass

    print(f"\n{'━'*60}\n")


def main():
    if len(sys.argv) < 2:
        print("Cara pakai: python scripts/find_owner.py <file|class|function>")
        print("Contoh:")
        print("  python scripts/find_owner.py cache/db.py")
        print("  python scripts/find_owner.py Database")
        print("  python scripts/find_owner.py publish")
        sys.exit(1)

    query = sys.argv[1]
    show_owner(query, PROJECT_ROOT)


if __name__ == "__main__":
    main()

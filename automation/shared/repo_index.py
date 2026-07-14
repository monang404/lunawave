"""
Module: automation.shared.repo_index

Purpose:
    Index AST satu kali untuk seluruh repo (classes, functions, imports, layer,
    event publish/subscribe, reverse-deps), dengan cache ber-invalidasi mtime.

Depends on:
    - automation.shared.skip_dirs (walk_py_files)

Subscribes to:
    None

Publishes:
    None
"""

from __future__ import annotations

import ast
import json
import time
from pathlib import Path

from shared.skip_dirs import walk_py_files

CACHE_PATH = Path(".cache/repo_index.json")
_BUS_METHODS = {"publish", "subscribe"}


def _event_name(node: ast.Call) -> str | None:
    """publish: bus.publish(DownloadCompleteEvent(...)) -> arg adalah Call.
    subscribe: bus.subscribe(DownloadCompleteEvent, handler) -> arg adalah Name."""
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Call) and isinstance(first.func, ast.Name):
        return first.func.id
    if isinstance(first, ast.Name):
        return first.id
    return None


def _parse_file(path: Path, root: Path) -> dict:
    rel = str(path.relative_to(root)).replace("\\", "/")
    source = path.read_text(encoding="utf-8", errors="replace")
    entry = {
        "layer": rel.split("/")[0] if "/" in rel else "root",
        "classes": [],
        "functions": [],
        "imports": [],
        "publishes": [],
        "subscribes": [],
        "loc": source.count("\n") + 1,
        "docstring_purpose": "",
    }
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return entry

    doc = ast.get_docstring(tree) or ""
    if "Purpose:" in doc:
        after = doc.split("Purpose:", 1)[1].lstrip("\n")
        entry["docstring_purpose"] = after.split("\n\n")[0].strip().replace("\n", " ")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            entry["classes"].append(node.name)  # type: ignore
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                entry["functions"].append(node.name)  # type: ignore
        elif isinstance(node, ast.Import):
            entry["imports"] += [a.name for a in node.names]  # type: ignore
        elif isinstance(node, ast.ImportFrom) and node.module:
            entry["imports"].append(node.module)  # type: ignore
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _BUS_METHODS:
                ev = _event_name(node)
                if ev:
                    key = "publishes" if node.func.attr == "publish" else "subscribes"
                    entry[key].append(ev)  # type: ignore
    return entry


def _rebuild_reverse_deps(files_index: dict) -> None:
    for entry in files_index.values():
        entry["reverse_deps"] = []
    for rel, entry in files_index.items():
        for imp in entry["imports"]:
            imp_path = imp.replace(".", "/") + ".py"
            if imp_path in files_index:
                files_index[imp_path]["reverse_deps"].append(rel)


def _load_or_build(root: Path, force: bool) -> dict:
    current = {
        str(p.relative_to(root)).replace("\\", "/"): p.stat().st_mtime for p in walk_py_files(root)
    }

    if not force and CACHE_PATH.exists():
        cached = json.loads(CACHE_PATH.read_text())
        old = cached["_meta"]["source_mtimes"]
        changed = {f for f, m in current.items() if old.get(f) != m}
        deleted = set(old) - set(current)
        if not changed and not deleted:
            return cached  # tidak ada yang berubah — pakai cache apa adanya

        files_index = cached["files"]
        for f in deleted:
            files_index.pop(f, None)
        for f in changed:  # <- hanya file berubah di-reparse
            files_index[f] = _parse_file(root / f, root)
    else:
        files_index = {f: _parse_file(root / f, root) for f in current}

    _rebuild_reverse_deps(files_index)  # murah: invert dict, bukan AST
    data = {"_meta": {"generated_at": time.time(), "source_mtimes": current}, "files": files_index}
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(data, indent=2))
    return data


def build_index(root: Path) -> dict:
    """Full rebuild — abaikan cache lama."""
    return _load_or_build(root, force=True)


def load_index(root: Path) -> dict:
    """Load dari cache; reparse hanya file yang mtime-nya berubah."""
    return _load_or_build(root, force=False)

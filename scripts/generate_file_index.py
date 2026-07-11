#!/usr/bin/env python3
"""
generate_file_index.py — Generate docs/FILE_INDEX.md dari source code.

Cara pakai:
    python scripts/generate_file_index.py
    python scripts/generate_file_index.py --dry-run   # preview ke stdout, tidak tulis file

Script ini HANYA mengganti blok di antara marker:
    <!-- BEGIN:GENERATED -->
    <!-- END:GENERATED -->

Bagian lain dari FILE_INDEX.md (header, catatan manual) dibiarkan utuh.
"""

import argparse
import ast
import os
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR    = Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_DIR.parent
DOCS_DIR      = PROJECT_ROOT / "docs"
FILE_INDEX_PATH = DOCS_DIR / "FILE_INDEX.md"

MARKER_BEGIN = "<!-- BEGIN:GENERATED -->"
MARKER_END   = "<!-- END:GENERATED -->"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from shared.skip_dirs import SKIP_DIRS
from shared.generated_block import replace_marker_block

# Folder yang di-scan (urut = urut tampil di output)
SCAN_GROUPS = [
    ("Root",       [""]),
    ("core/",      ["core"]),
    ("engine/",    ["engine", "engine/playback"]),
    ("cache/",     ["cache"]),
    ("server/",    ["server", "server/handlers", "server/services"]),
    ("services/",  ["services"]),
    ("plugins/",   ["plugins"]),
    ("launcher/",  ["launcher"]),
    ("data/",      ["data"]),
    ("scripts/",   ["scripts"]),
    ("scripts/shared",["scripts/shared"]),
    ("scripts/verify_docs",["scripts/verify_docs"]),
]


# ---------------------------------------------------------------------------
# AST Extraction
# ---------------------------------------------------------------------------

PURPOSE_RE = re.compile(
    r"^\s*Purpose\s*:\s*(.+(?:\n(?!\s*(?:Subscribes to|Publishes)\s*:)(?!\s*$).+)*)",
    re.IGNORECASE | re.MULTILINE,
)

NO_DOCSTRING_LABEL = "⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_"


def extract_purpose(tree: ast.AST) -> tuple[str | None, bool]:
    doc = ast.get_docstring(tree)
    if not doc:
        return None, False
    m = PURPOSE_RE.search(doc)
    if not m:
        return None, False
    joined = " ".join(line.strip() for line in m.group(1).splitlines())
    return joined.strip(), True


def extract_module_info(path: Path) -> dict:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree   = ast.parse(source, filename=str(path))
    except SyntaxError:
        return {
            "classes": [], "functions": [], "imports": [],
            "purpose": None, "has_docstring": False,
        }

    purpose, has_docstring = extract_purpose(tree)

    classes   = []
    functions = []
    imports   = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(f"{b.attr}")
            if bases:
                classes.append(f"{node.name}({', '.join(bases)})")
            else:
                classes.append(node.name)

            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef) and not child.name.startswith("__"):
                    functions.append(f"{child.name}()")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(f"{node.name}()")

        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    seen       = set()
    uniq_imports = []
    for i in imports:
        if i not in seen:
            seen.add(i)
            uniq_imports.append(i)

    return {
        "classes": classes,
        "functions": functions,
        "imports": uniq_imports,
        "purpose": purpose,
        "has_docstring": has_docstring,
    }


def collect_py_files(project_root: Path) -> list[Path]:
    result = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                result.append(Path(dirpath) / fn)
    return sorted(result)


def build_reverse_index(all_files: list[Path], project_root: Path) -> dict[str, list[str]]:
    rev: dict[str, list[str]] = {}

    for path in all_files:
        rel     = path.relative_to(project_root)
        rel_str = str(rel).replace("\\", "/")
        info    = extract_module_info(path)
        importer = rel_str.removesuffix(".py")

        for imp in info["imports"]:
            imp_as_path = imp.replace(".", "/")
            candidates  = [
                imp_as_path + ".py",
                imp_as_path + "/__init__.py",
            ]
            found = any((project_root / c).exists() for c in candidates)
            if found:
                rev.setdefault(imp_as_path, []).append(importer)

    return rev


# ---------------------------------------------------------------------------
# Format output per file
# ---------------------------------------------------------------------------

def format_file_entry(
    rel_path: str,
    info: dict,
    rev_index: dict[str, list[str]],
) -> str:
    fungsi_str = info["purpose"] if info["purpose"] else NO_DOCSTRING_LABEL

    classes_str = ", ".join(f"`{c}`" for c in info["classes"]) if info["classes"] else "—"

    pub_fns  = [f for f in info["functions"] if not f.startswith("_")]
    priv_fns = [f for f in info["functions"] if f.startswith("_") and not f.startswith("__")]
    shown_fns = pub_fns[:6]
    if not shown_fns and priv_fns:
        shown_fns = priv_fns[:4]
    functions_str = ", ".join(f"`{f}`" for f in shown_fns) if shown_fns else "—"

    internal_imports = []
    for imp in info["imports"]:
        imp_path   = imp.replace(".", "/")
        candidates = [imp_path + ".py", imp_path + "/__init__.py"]
        if any(True for c in candidates if (PROJECT_ROOT / c).exists()):
            internal_imports.append(f"`{imp_path}`")
    using_str = ", ".join(internal_imports[:6]) if internal_imports else "—"
    if len(internal_imports) > 6:
        using_str += f", _{len(internal_imports) - 6} lainnya_"

    key    = rel_path.removesuffix(".py")
    users  = rev_index.get(key, [])
    if users:
        used_by_str = ", ".join(f"`{u}`" for u in sorted(users)[:5])
        if len(users) > 5:
            used_by_str += f", _{len(users) - 5} lainnya_"
    else:
        used_by_str = "—"

    return (
        f"**File:** `{rel_path}`  \n"
        f"**Fungsi:** {fungsi_str}  \n"
        f"**Class:** {classes_str}  \n"
        f"**Function utama:** {functions_str}  \n"
        f"**Digunakan oleh:** {used_by_str}  \n"
        f"**Menggunakan:** {using_str}\n"
    )


# ---------------------------------------------------------------------------
# Build generated block
# ---------------------------------------------------------------------------

def build_generated_block(project_root: Path) -> str:
    all_files = collect_py_files(project_root)
    rev_index = build_reverse_index(all_files, project_root)

    file_info: dict[str, dict] = {}
    for path in all_files:
        rel = str(path.relative_to(project_root)).replace("\\", "/")
        file_info[rel] = extract_module_info(path)

    lines = [
        f"> **Auto-generated:** {date.today().isoformat()} oleh `scripts/generate_file_index.py`  \n"
        f"> **Jangan edit blok ini secara manual** — perubahan akan ditimpa saat script dijalankan ulang.\n",
    ]

    for group_name, folders in SCAN_GROUPS:
        group_files = []
        for folder in folders:
            prefix = folder + "/" if folder else ""
            for rel_path, info in file_info.items():
                if folder == "":
                    if "/" not in rel_path and rel_path.endswith(".py"):
                        group_files.append((rel_path, info))
                else:
                    if rel_path.startswith(prefix):
                        remainder = rel_path[len(prefix):]
                        if "/" not in remainder and rel_path.endswith(".py"):
                            group_files.append((rel_path, info))

        if not group_files:
            continue

        lines.append(f"\n## {group_name}\n")
        for rel_path, info in sorted(group_files):
            if rel_path.endswith("__init__.py") and not info["classes"] and not info["functions"]:
                continue
            lines.append(format_file_entry(rel_path, info, rev_index))
            lines.append("\n---\n")

    big_files = [
        (rel, sum(1 for _ in (project_root / rel).read_text(encoding="utf-8", errors="replace").splitlines()))
        for rel in file_info
        if rel.endswith(".py") and not rel.endswith("__init__.py")
    ]
    big_files = [(r, n) for r, n in big_files if n > 200]
    big_files.sort(key=lambda x: -x[1])

    if big_files:
        lines.append("\n## ⚠️ File Besar (>200 baris)\n\n")
        lines.append("| File | Baris | Catatan |\n|---|---|---|\n")
        for rel, n in big_files:
            note = "Perlu dipecah" if n > 350 else "Perhatikan"
            lines.append(f"| `{rel}` | {n} | {note} |\n")

    missing_doc = sorted(
        rel for rel, info in file_info.items()
        if not info["has_docstring"] and not rel.endswith("__init__.py")
    )
    total_py   = sum(1 for rel in file_info if not rel.endswith("__init__.py"))
    documented = total_py - len(missing_doc)
    lines.append(
        f"\n## 📋 Checklist Dokumentasi Docstring\n\n"
        f"**{documented}/{total_py}** file `.py` sudah punya docstring modul terstruktur "
        f"(`Purpose:` / `Subscribes to:` / `Publishes:`). Berikut yang belum:\n\n"
    )
    if missing_doc:
        for rel in missing_doc:
            lines.append(f"- [ ] `{rel}`\n")
    else:
        lines.append("_(semua file sudah terdokumentasi 🎉)_\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Inject ke FILE_INDEX.md
# ---------------------------------------------------------------------------

def inject_into_file(target: Path, generated_block: str, dry_run: bool) -> None:
    original = target.read_text(encoding="utf-8")

    if MARKER_BEGIN not in original:
        # Fallback lokal: append di akhir file
        new_content = original.rstrip() + f"\n\n{MARKER_BEGIN}\n{generated_block}\n{MARKER_END}\n"
    else:
        new_content = replace_marker_block(original, generated_block, MARKER_BEGIN, MARKER_END)

    # Update frontmatter last_verified
    new_content = re.sub(
        r"(last_verified:\s*)\d{4}-\d{2}-\d{2}",
        f"\\g<1>{date.today().isoformat()}",
        new_content,
        count=1,
    )
    # Update warning di frontmatter
    new_content = new_content.replace(
        "warning: file ini manual — mungkin stale. re-verify sebelum dipakai.",
        "generated: sebagian blok ini di-generate otomatis. lihat marker BEGIN/END:GENERATED.",
    )

    if dry_run:
        print(new_content)
    else:
        target.write_text(new_content, encoding="utf-8")
        print(f"✅ {target.relative_to(PROJECT_ROOT)} diperbarui ({date.today().isoformat()})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate FILE_INDEX.md dari AST source code.")
    parser.add_argument("--dry-run", action="store_true", help="Print ke stdout, tidak tulis file")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="Override project root")
    args = parser.parse_args()

    root   = Path(args.project_root).resolve()
    target = root / "docs" / "FILE_INDEX.md"

    if not target.exists():
        print(f"❌ FILE_INDEX.md tidak ditemukan: {target}", file=sys.stderr)
        sys.exit(1)

    print("🔍 Scanning source files...", file=sys.stderr)
    block = build_generated_block(root)

    inject_into_file(target, block, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

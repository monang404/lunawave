#!/usr/bin/env python3
"""
Module: automation.patchlog

Purpose:
    Baca/tulis docs/PATCHLOG.md terstruktur. ID PATCH-YYYY-MM-DD-NNN, NNN = total
    entries berjalan (bukan reset per hari).

CLI:
    python automation/patchlog.py add "<deskripsi>" --files a.py,b.py
    python automation/patchlog.py latest --n 5 [--json]
    python automation/patchlog.py history --file <path> [--json]
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

PATCHLOG = PROJECT_ROOT / "docs" / "PATCHLOG.md"

ENTRY_RE = re.compile(
    r"\*\*ID:\*\* `(?P<id>PATCH-[\d-]+)`.*?"
    r"\*\*Tanggal:\*\* (?P<tanggal>[\d-]+).*?"
    r"\*\*Ringkasan:\*\* (?P<ringkasan>.+?)\n.*?"
    r"\*\*File Terdampak:\*\*.*?\n\n(?P<files>(?:- .+\n?)+)",
    re.DOTALL,
)


def parse_entries(text: str) -> list[dict]:
    entries = []
    for m in ENTRY_RE.finditer(text):
        files = re.findall(r"- `([^`]+)`", m.group("files"))
        entries.append(
            {
                "id": m.group("id"),
                "tanggal": m.group("tanggal"),
                "ringkasan": m.group("ringkasan").strip(),
                "files": files,
            }
        )
    return entries


def add_entry(desc: str, files: list[str]) -> str:
    text = PATCHLOG.read_text(encoding="utf-8")
    entries = parse_entries(text)
    new_id = f"PATCH-{date.today().isoformat()}-{len(entries) + 1:03d}"
    files_block = "\n".join(f"- `{f}`" for f in files)
    block = (
        f"\n## [{date.today().isoformat()}] {desc}\n\n"
        f"**ID:** `{new_id}`\n\n**Tanggal:** {date.today().isoformat()}\n\n"
        f"**Ringkasan:** {desc}\n\n**File Terdampak:**\n\n{files_block}\n\n---\n"
    )
    marker = "---\n\n"  # tepat setelah blockquote format-notice
    idx = text.index(marker) + len(marker)
    new_text = text[:idx] + block + text[idx:]
    new_text = re.sub(r"latest_patch_id:.*", f"latest_patch_id: {new_id}", new_text, count=1)
    new_text = re.sub(r"total_entries:.*", f"total_entries: {len(entries) + 1}", new_text, count=1)
    PATCHLOG.write_text(new_text, encoding="utf-8")
    return new_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("description")
    p_add.add_argument("--files", required=True, help="Comma-separated")

    p_latest = sub.add_parser("latest")
    p_latest.add_argument("--n", type=int, default=5)
    p_latest.add_argument("--json", action="store_true", dest="json_output")

    p_hist = sub.add_parser("history")
    p_hist.add_argument("--file", required=True)
    p_hist.add_argument("--json", action="store_true", dest="json_output")

    args = parser.parse_args()

    if args.cmd == "add":
        print(f"Ditambahkan: {add_entry(args.description, args.files.split(','))}")
        return

    entries = parse_entries(PATCHLOG.read_text(encoding="utf-8"))
    result = (
        entries[: args.n]
        if args.cmd == "latest"
        else [e for e in entries if args.file in e["files"]]
    )
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))  # Original spec used json.dumps or raw list


if __name__ == "__main__":
    main()

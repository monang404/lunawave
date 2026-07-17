#!/usr/bin/env python3
"""
Module: automation.patchlog

Purpose:
    Baca/tulis docs/PATCHLOG.md terstruktur. ID PATCH-YYYY-MM-DD-NNN, NNN = total
    entries berjalan (bukan reset per hari).

Subscribes to:
    None

Publishes:
    None

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

ENTRY_ID_RE = re.compile(r"\*\*ID:\*\* `(?P<id>PATCH-[\d-]+)`")
ENTRY_TANGGAL_RE = re.compile(r"\*\*Tanggal:\*\* (?P<tanggal>[\d-]+)")
ENTRY_RINGKASAN_RE = re.compile(r"\*\*Ringkasan:\*\* (?P<ringkasan>.+)")
ENTRY_FILES_BLOCK_RE = re.compile(r"\*\*File Terdampak:\*\*\n(?P<files>(?:- .+\n?)+)")


def parse_entries(text: str) -> list[dict]:
    # PATCH-2026-07-16-001: sebelumnya satu regex DOTALL raksasa (ID ->
    # Tanggal -> Ringkasan -> File Terdampak, semuanya via `.*?` lazy)
    # di-scan ke SELURUH file sekaligus. Dengan struktur berulang 68x
    # entry yang mirip satu sama lain, ini catastrophic backtracking --
    # dikonfirmasi hang tak terhingga di docs/PATCHLOG.md nyata (35KB).
    # Fix: split per-entry dulu pakai separator baris "---", baru regex
    # SEDERHANA (non-DOTALL-spanning-banyak-entry) per-chunk. Tiap chunk
    # kecil (~500 byte) jadi tidak ada ruang untuk backtracking meledak.
    entries = []
    for chunk in text.split("\n\n---\n\n"):
        id_m = ENTRY_ID_RE.search(chunk)
        if not id_m:
            continue
        tanggal_m = ENTRY_TANGGAL_RE.search(chunk)
        ringkasan_m = ENTRY_RINGKASAN_RE.search(chunk)
        files_m = ENTRY_FILES_BLOCK_RE.search(chunk)
        if not (tanggal_m and ringkasan_m and files_m):
            continue
        files = re.findall(r"- `([^`]+)`", files_m.group("files"))
        entries.append(
            {
                "id": id_m.group("id"),
                "tanggal": tanggal_m.group("tanggal"),
                "ringkasan": ringkasan_m.group("ringkasan").strip(),
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
    # PENTING: file diawali frontmatter YAML yang juga dibuka/ditutup dengan "---".
    # text.index(marker) tanpa offset akan selalu cocok dengan "---\n\n" di baris
    # pertama (pembuka frontmatter), bukan garis horizontal setelah blockquote —
    # ini menyebabkan entry baru disisipkan DI DALAM frontmatter dan merusaknya.
    # Lewati dulu blok frontmatter (jika ada) sebelum mencari marker sungguhan.
    search_start = 0
    if text.startswith("---"):
        fm_close = text.find("\n---", 3)
        if fm_close != -1:
            search_start = fm_close + len("\n---")
    idx = text.index(marker, search_start) + len(marker)
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

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
    python automation/patchlog.py verify [--json]
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

ALL_ID_RE = re.compile(r"\*\*ID:\*\* `(?P<id>PATCH-\d{4}-\d{2}-\d{2}-\d{3})`")
ENTRY_ID_RE = ALL_ID_RE
ENTRY_TANGGAL_RE = re.compile(r"\*\*Tanggal:\*\*\s*(?P<tanggal>[\d-]+)")
# Ringkasan boleh di baris yang sama ("**Ringkasan:** teks...") ATAU di
# baris berikutnya kalau ditulis manual ("**Ringkasan:**\nteks...\nteks
# lanjutan..."). Ambil semua baris sampai baris kosong atau field berikutnya.
ENTRY_RINGKASAN_RE = re.compile(
    r"\*\*Ringkasan:\*\*[ \t]*\n?(?P<ringkasan>.+?)(?=\n\s*\n|\n\*\*File Terdampak|\Z)",
    re.DOTALL,
)
ENTRY_FILES_BLOCK_RE = re.compile(r"\*\*File Terdampak:\*\*\n+(?P<files>(?:-[^\n]*\n?)+)")


def _split_into_chunks(text: str) -> list[str]:
    """Pecah body PATCHLOG per-entry.

    PATCH-2026-07-16-001: split via separator "\\n\\n---\\n\\n" untuk hindari
    catastrophic backtracking dari regex DOTALL raksasa lama. PATCH-2026-07-17-074:
    separator itu ternyata rapuh -- entry yang ditulis manual (tanpa baris
    kosong presisi di sekitar "---") gagal ke-split dan diam-diam MENGHILANG
    (5 entry hilang tanpa error/warning di docs/PATCHLOG.md nyata). Fix: split
    di setiap baris "---" berdiri sendiri (toleran spasi di sekitarnya).
    Masih O(n) per chunk kecil -- tidak membuka lagi celah backtracking 001.
    """
    return re.split(r"\n[ \t]*---[ \t]*\n", text)


def parse_entries(text: str) -> list[dict]:
    entries = []
    for chunk in _split_into_chunks(text):
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
                "ringkasan": " ".join(ringkasan_m.group("ringkasan").split()).strip(),
                "files": files,
            }
        )
    return entries


def verify(text: str) -> dict:
    """Bandingkan ID yang ADA di file vs ID yang berhasil di-parse penuh.

    Sebelum PATCH-2026-07-17-074, entry yang gagal parsing (format tidak
    baku) hilang dari `parse_entries()` TANPA sinyal apapun -- konsumen
    seperti context_pack.py/find_owner.py diam-diam kehilangan riwayat
    entry itu. Dipakai automation/verify_docs.py untuk menangkap kasus ini
    sebagai FAIL, bukan cuma "ID unik & berurutan".
    """
    all_ids = ALL_ID_RE.findall(text)
    parsed_ids = {e["id"] for e in parse_entries(text)}
    missing = [pid for pid in all_ids if pid not in parsed_ids]
    return {
        "total_ids_found": len(all_ids),
        "total_parsed": len(parsed_ids),
        "unparsed_ids": missing,
        "ok": not missing,
    }


def _next_id(entries: list[dict]) -> str:
    # PATCH-2026-07-17-074: `len(entries) + 1` salah kalau parse_entries()
    # kehilangan entry (lihat bug di atas) -- menghasilkan ID yang sudah
    # dipakai (tabrakan). Pakai NNN tertinggi dari SEMUA ID yang ada di
    # file (bukan cuma yang ke-parse penuh) + 1, supaya tetap benar walau
    # ada entry lama berformat rusak.
    all_ids = ALL_ID_RE.findall(PATCHLOG.read_text(encoding="utf-8"))
    seqs = [int(pid.rsplit("-", 1)[1]) for pid in all_ids]
    next_seq = (max(seqs) + 1) if seqs else (len(entries) + 1)
    return f"PATCH-{date.today().isoformat()}-{next_seq:03d}"


def add_entry(desc: str, files: list[str]) -> str:
    text = PATCHLOG.read_text(encoding="utf-8")
    entries = parse_entries(text)
    new_id = _next_id(entries)
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
    # total_entries dihitung dari SEMUA ID di file (sama seperti _next_id),
    # bukan len(entries) yang bisa lebih kecil dari jumlah asli kalau ada
    # entry lama gagal parse -- lihat PATCH-2026-07-17-074.
    total = len(ALL_ID_RE.findall(new_text))
    new_text = re.sub(r"latest_patch_id:.*", f"latest_patch_id: {new_id}", new_text, count=1)
    new_text = re.sub(r"total_entries:.*", f"total_entries: {total}", new_text, count=1)
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

    p_verify = sub.add_parser("verify", help="Cek entry yang gagal di-parse (format rusak)")
    p_verify.add_argument("--json", action="store_true", dest="json_output")

    args = parser.parse_args()

    if args.cmd == "add":
        print(f"Ditambahkan: {add_entry(args.description, args.files.split(','))}")
        return

    text = PATCHLOG.read_text(encoding="utf-8")

    if args.cmd == "verify":
        report = verify(text)
        if args.json_output:
            print(json.dumps(report, indent=2))
        else:
            print(f"ID ditemukan   : {report['total_ids_found']}")
            print(f"Berhasil parse : {report['total_parsed']}")
            if report["unparsed_ids"]:
                print(f"❌ Gagal parse ({len(report['unparsed_ids'])}):")
                for pid in report["unparsed_ids"]:
                    print(f"   - {pid}")
                sys.exit(1)
            print("✅ Semua entry berhasil di-parse.")
        return

    entries = parse_entries(text)
    result = (
        entries[: args.n]
        if args.cmd == "latest"
        else [e for e in entries if args.file in e["files"]]
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

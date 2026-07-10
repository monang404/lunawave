#!/usr/bin/env python3
"""
validate_docs.py — Pemeriksa kesehatan dokumentasi LunaWave.

Ini BUKAN linter markdown biasa. Script ini khusus ngecek 3 hal yang
gampang basi/rusak kalau diupdate manual terus-terusan:

  1. PATCHLOG.md   — apakah semua ID unik & formatnya benar, dan apakah
                      `latest_patch_id` di frontmatter cocok sama entry terakhir?
  2. Frontmatter    — apakah setiap dokumen di docs/ punya `last_verified`,
                      dan apakah tanggalnya masih segar (< N hari)?
  3. Referensi file — apakah path file yang disebut di STATUS.md / REPORT.md /
                      dokumen lain (dalam backtick) benar-benar ada di project?

Cara pakai (boleh dijalankan dari mana saja — root project ATAU dari
dalam folder scripts/ itu sendiri; default docs-dir & project-root
dihitung dari lokasi script ini, bukan dari folder tempat kamu ngetik
command):

    python scripts/verify_docs.py          # dari root project
    cd scripts && python verify_docs.py    # dari dalam scripts/, hasilnya sama
    python scripts/verify_docs.py --stale-days 14
    python scripts/verify_docs.py --include-kompas
    python scripts/verify_docs.py --docs-dir /path/lain/docs --project-root /path/lain

Exit code: 0 kalau tidak ada masalah kategori ❌ (error).
           1 kalau ada minimal 1 ❌. (Berguna kalau nanti mau dipasang
           sebagai git pre-commit hook.)

Keterbatasan yang perlu disadari (baca ini sebelum panik lihat outputnya):
  - Script ini TIDAK tahu mana "belum ada" yang memang disengaja
    (misal docs/CONSTRAINTS.md yang statusnya ⏳ Belum di STATUS.md)
    vs yang beneran salah ketik/lupa update. Semua "missing path"
    tetap dilaporkan — kamu yang menilai mana yang expected.
  - Deteksi "path file" pakai heuristik (isi backtick yang mengandung
    "/" atau ".") — bukan parser markdown penuh. Sudah difilter dari
    cuplikan kode (`fn()`), penyebutan ekstensi generik (`.py`), route
    HTTP (`/health`), dan notasi module.attribute (`werkzeug.security`).
    Referensi tanpa ekstensi (`core/event_bus`) atau basename doang
    (`state.py`, gaya tree-listing) dicek dengan menebak ekstensi umum
    dan mencari di seluruh project — tapi ini tetap heuristik, bukan
    parser AST/import resolver, jadi bukan 100% presisi.
  - Kalau docs/ dan source code project TIDAK ada di lokasi normal relatif
    ke script ini (`<project_root>/scripts/verify_docs.py` dan
    `<project_root>/docs/`), atau kamu memang mau nunjuk ke folder lain,
    pakai --docs-dir dan --project-root eksplisit.
"""

import argparse
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

# Lokasi script ini sendiri (mis. <project_root>/scripts/verify_docs.py).
# Dipakai buat nentuin default docs-dir & project-root SUPAYA TIDAK
# tergantung dari mana kamu menjalankan script-nya (cwd) — jadi tetap benar
# baik dijalankan dari root project (`python scripts/verify_docs.py`)
# maupun dari dalam folder scripts/ itu sendiri (`python verify_docs.py`).
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_DOCS_DIR = DEFAULT_PROJECT_ROOT / "docs"

PATCH_ID_RE = re.compile(r"\*\*ID:\*\*\s*`(PATCH-\d{4}-\d{2}-\d{2}-\d{3})`")
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
PURE_VERSION_RE = re.compile(r"^[\d.]+$")  # contoh: "3.2", "1.0" — bukan path

# Ekstensi generik yang sering disebut TANPA nama file di depannya, misal
# "total file `.py`" atau "ekskl. `.git`" — itu bukan path, cuma nyebut tipe file.
GENERIC_EXTENSION_MENTIONS = {
    "py", "js", "jsx", "ts", "tsx", "css", "scss", "html", "htm", "json",
    "sql", "txt", "md", "sh", "bat", "yml", "yaml", "xml", "git",
}

# Ekstensi yang dianggap "file beneran" kalau muncul di akhir path/basename.
KNOWN_FILE_EXTENSIONS = {
    "py", "js", "jsx", "ts", "tsx", "css", "scss", "html", "htm", "json",
    "sql", "txt", "md", "sh", "bat", "yml", "yaml", "toml", "cfg", "ini",
    "xml", "db", "log", "conf", "service", "env",
}

# Kalau nemu path tanpa ekstensi (gaya penyebutan modul, misal "core/event_bus"),
# coba tempel salah satu ekstensi ini buat lihat apakah file aslinya ada.
EXTENSIONS_TO_GUESS = ["py", "js", "ts", "css", "md", "sql", "json", "txt", "html"]

# Notasi "module.attribute"/"module.function" tanpa slash, misal "werkzeug.security"
# atau "asyncio.sleep" — dua identifier dipisah satu titik, TIDAK diawali titik
# (jadi bukan dotfile seperti ".editorconfig") dan tidak ada tanda hubung/angka
# aneh (jadi bukan nama file majemuk seperti "lunawave.db-shm").
DOTTED_ATTR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")

# Folder yang dilewati saat membangun index nama file (noise / hasil build).
NOISE_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache", ".tox"}


# ---------------------------------------------------------------------------
# Util kecil
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> dict | None:
    """Ambil isi frontmatter --- ... --- di baris paling atas file (kalau ada)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm


def looks_like_path(candidate: str) -> str | None:
    """Heuristik: apakah isi backtick ini kemungkinan path file/folder?
    Return path yang sudah dibersihkan (tanpa suffix :L47,L64 dsb), atau None."""
    c = candidate.strip()
    if not c or " " in c:
        return None
    if PURE_VERSION_RE.match(c):
        return None
    if "/" not in c and "." not in c:
        return None
    if c.endswith("*") or "*" in c:  # pola env var seperti LUNAWAVE_*
        return None
    if c.startswith("http://") or c.startswith("https://"):
        return None
    # cuplikan kode seperti `asyncio.run()`, `db.get_track()`, `ServerManager(tk.Tk)`
    # — ini pemanggilan fungsi/class, bukan path file.
    if "(" in c or ")" in c:
        return None
    # penyebutan ekstensi generik doang, misal "total file `.py`" atau
    # "ekskl. `.git`" — bukan path ke file spesifik.
    if c.startswith(".") and c[1:].lower() in GENERIC_EXTENSION_MENTIONS:
        return None
    # endpoint HTTP/WS seperti `/stream`, `/health`, `/auth/login` — bukan path
    # filesystem relatif terhadap project root (yang di sini tidak pernah pakai
    # leading slash), jadi kalau tidak ada ekstensi file, anggap itu route.
    if c.startswith("/") and "." not in c:
        return None
    # buang suffix "path/to/file.py:L47,L64" -> "path/to/file.py"
    c = c.split(":")[0]
    return c


# ---------------------------------------------------------------------------
# Cek 1 — PATCHLOG ID unik, valid, dan sinkron dengan frontmatter
# ---------------------------------------------------------------------------

def check_patchlog(docs_dir: Path) -> tuple[list[str], list[str], list[str]]:
    ok, warn, err = [], [], []
    patchlog = docs_dir / "PATCHLOG.md"
    if not patchlog.exists():
        err.append("PATCHLOG.md tidak ditemukan di docs/.")
        return ok, warn, err

    text = read_text(patchlog)
    ids = PATCH_ID_RE.findall(text)

    if not ids:
        warn.append("PATCHLOG.md: tidak ada entry dengan format **ID:** `PATCH-YYYY-MM-DD-NNN` ditemukan.")
        return ok, warn, err

    # unik?
    seen = set()
    dupes = set()
    for pid in ids:
        if pid in seen:
            dupes.add(pid)
        seen.add(pid)
    if dupes:
        err.append(f"PATCHLOG.md: ID duplikat ditemukan: {', '.join(sorted(dupes))}")
    else:
        ok.append(f"PATCHLOG.md: {len(ids)} entry, semua ID unik & formatnya valid.")

    # cocok sama frontmatter latest_patch_id?
    fm = parse_frontmatter(text)
    last_id_in_body = ids[-1]
    if fm is None:
        warn.append("PATCHLOG.md: tidak ada frontmatter (last_verified/latest_patch_id).")
    else:
        latest_fm = fm.get("latest_patch_id")
        if latest_fm is None:
            warn.append("PATCHLOG.md: frontmatter tidak punya field 'latest_patch_id'.")
        elif latest_fm != last_id_in_body:
            err.append(
                f"PATCHLOG.md: frontmatter latest_patch_id='{latest_fm}' "
                f"TIDAK COCOK dengan entry terakhir di body ('{last_id_in_body}'). "
                f"Kemungkinan ada entry baru yang lupa diupdate ke frontmatter."
            )
        else:
            ok.append(f"PATCHLOG.md: latest_patch_id frontmatter cocok dengan entry terakhir ({last_id_in_body}).")

    return ok, warn, err


# ---------------------------------------------------------------------------
# Cek 2 — Frontmatter ada & masih segar di semua dokumen
# ---------------------------------------------------------------------------

def check_frontmatter_freshness(docs_dir: Path, stale_days: int, include_kompas: bool) -> tuple[list, list, list]:
    ok, warn, err = [], [], []
    md_files = sorted(docs_dir.glob("*.md"))
    if include_kompas:
        md_files += sorted((docs_dir / "kompas").rglob("*.md"))

    today = date.today()
    for f in md_files:
        text = read_text(f)
        fm = parse_frontmatter(text)
        rel = f.relative_to(docs_dir.parent)
        if fm is None:
            warn.append(f"{rel}: tidak punya frontmatter (--- last_verified: ... ---) di baris paling atas.")
            continue
        lv = fm.get("last_verified")
        if lv is None:
            warn.append(f"{rel}: frontmatter ada, tapi field 'last_verified' tidak ditemukan.")
            continue
        try:
            lv_date = datetime.strptime(lv, "%Y-%m-%d").date()
        except ValueError:
            err.append(f"{rel}: format last_verified='{lv}' tidak valid (harus YYYY-MM-DD).")
            continue
        age = (today - lv_date).days
        if age < 0:
            warn.append(f"{rel}: last_verified={lv} adalah tanggal masa depan — cek typo tahun.")
        elif age > stale_days:
            warn.append(f"{rel}: last_verified={lv} sudah {age} hari lalu (ambang: {stale_days} hari) — perlu re-verify.")
        else:
            ok.append(f"{rel}: frontmatter segar (last_verified {age} hari lalu).")

    return ok, warn, err


# ---------------------------------------------------------------------------
# Cek 3 — Path file yang disebut di dokumen benar-benar ada di project
# ---------------------------------------------------------------------------

def build_basename_index(project_root: Path) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    """Index semua nama file & folder di project (basename -> daftar path
    relatif). Dipakai buat fallback: dokumen gaya tree-listing sering cuma
    nyebut nama file/folder doang ('state.py', 'components/') tanpa path
    lengkap di depannya ('core/state.py', 'web/static/css/components/')."""
    file_index: dict[str, list[Path]] = {}
    dir_index: dict[str, list[Path]] = {}
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in NOISE_DIRS]
        for d in dirnames:
            rel = (Path(dirpath) / d).relative_to(project_root)
            dir_index.setdefault(d, []).append(rel)
        for fn in filenames:
            rel = (Path(dirpath) / fn).relative_to(project_root)
            file_index.setdefault(fn, []).append(rel)
    return file_index, dir_index


def resolve_candidate(
    candidate: str,
    bases: list[Path],
    file_index: dict[str, list[Path]],
    dir_index: dict[str, list[Path]],
) -> bool | None:
    """Coba cari `candidate` di beberapa base dir (project_root, docs_dir,
    folder dokumen itu sendiri). Return True (ketemu), False (tidak ketemu,
    perlu dilaporkan), atau None (bukan path — abaikan, jangan hitung sama
    sekali, misal ini ternyata dotted attribute/module reference)."""
    for b in bases:
        if (b / candidate).exists():
            return True

    if candidate.endswith("/"):
        # referensi folder — gaya tree-listing sering cuma nyebut nama folder
        # doang ("components/") tanpa path lengkap di depannya. Coba cari di
        # seluruh project kalau namanya tidak mengandung "/" sama sekali.
        bare_dir = candidate.rstrip("/")
        if "/" not in bare_dir and bare_dir in dir_index:
            return True
        return False

    last_seg = candidate.rsplit("/", 1)[-1]

    if "." in last_seg:
        suffix = last_seg.rsplit(".", 1)[-1].lower()
        if suffix in KNOWN_FILE_EXTENSIONS:
            # basename dengan ekstensi valid tapi tidak ketemu langsung —
            # coba cari di mana saja di project (gaya tree-listing).
            if "/" not in candidate and last_seg in file_index:
                return True
            return False
        # akhiran bukan ekstensi file yang dikenal -> kemungkinan besar ini
        # notasi "module.attribute"/"module.function" (mis. `core/security.hash_password`,
        # atau `werkzeug.security`), bukan path literal. Coba tebak sebagai
        # "prefix" + ekstensi kode dulu.
        prefix = candidate.rsplit(".", 1)[0]
        for ext in EXTENSIONS_TO_GUESS:
            for b in bases:
                if (b / f"{prefix}.{ext}").exists():
                    return True
        if "/" not in candidate and DOTTED_ATTR_RE.match(candidate):
            # pola persis "word.word" tanpa slash (mis. "werkzeug.security") ->
            # ini kemungkinan besar referensi import/atribut, bukan path project.
            return None
        # selain itu (dotfile seperti ".editorconfig", atau nama file majemuk
        # seperti "lunawave.db-shm") — ini tetap kandidat path yang sah, cuma
        # kebetulan tidak ketemu.
        return False

    # tidak ada ekstensi sama sekali tapi ada "/", gaya penyebutan modul
    # (mis. "core/event_bus", "engine/mpv_controller") — coba tebak ekstensinya.
    for ext in EXTENSIONS_TO_GUESS:
        for b in bases:
            if (b / f"{candidate}.{ext}").exists():
                return True
    return False


def check_file_references(docs_dir: Path, project_root: Path, include_kompas: bool) -> tuple[list, list, list]:
    ok, warn, err = [], [], []
    md_files = sorted(docs_dir.glob("*.md"))
    if include_kompas:
        md_files += sorted((docs_dir / "kompas").rglob("*.md"))

    file_index, dir_index = build_basename_index(project_root)

    total_checked = 0
    total_ignored = 0
    for f in md_files:
        text = read_text(f)
        rel_doc = f.relative_to(docs_dir.parent)
        bases = [project_root, docs_dir, f.parent]
        for line_no, line in enumerate(text.splitlines(), start=1):
            for raw in BACKTICK_RE.findall(line):
                candidate = looks_like_path(raw)
                if candidate is None:
                    continue
                result = resolve_candidate(candidate, bases, file_index, dir_index)
                if result is None:
                    total_ignored += 1
                    continue
                total_checked += 1
                if not result:
                    warn.append(f"{rel_doc}:{line_no} — path `{candidate}` disebut tapi tidak ditemukan di project.")

    if total_checked == 0:
        warn.append("Tidak ada kandidat path yang terdeteksi untuk dicek (cek heuristik atau isi dokumen).")
    else:
        found_issues = len(warn)
        extra = f" ({total_ignored} kandidat diabaikan karena bukan path, mis. referensi module/atribut)." if total_ignored else ""
        ok.append(f"{total_checked} referensi path dicek, {total_checked - found_issues} ditemukan cocok.{extra}")

    return ok, warn, err


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validator kesehatan docs/ LunaWave.")
    parser.add_argument(
        "--docs-dir", default=str(DEFAULT_DOCS_DIR),
        help=f"Folder docs (default: {DEFAULT_DOCS_DIR}, dihitung dari lokasi script ini, bukan cwd)",
    )
    parser.add_argument(
        "--project-root", default=str(DEFAULT_PROJECT_ROOT),
        help=f"Root project untuk cek path file (default: {DEFAULT_PROJECT_ROOT}, dihitung dari lokasi script ini, bukan cwd)",
    )
    parser.add_argument("--stale-days", type=int, default=30, help="Ambang hari sebelum last_verified dianggap basi (default: 30)")
    parser.add_argument("--include-kompas", action="store_true", help="Ikut cek docs/kompas/ juga (default: tidak, karena isinya blueprint aspirational)")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir).resolve()
    project_root = Path(args.project_root).resolve()

    if not docs_dir.exists():
        print(f"❌ Folder docs tidak ditemukan: {docs_dir}")
        sys.exit(1)

    sections = [
        ("1. PATCHLOG — ID unik & sinkron frontmatter", check_patchlog(docs_dir)),
        ("2. Frontmatter — ada & masih segar", check_frontmatter_freshness(docs_dir, args.stale_days, args.include_kompas)),
        ("3. Referensi path file — masih valid", check_file_references(docs_dir, project_root, args.include_kompas)),
    ]

    total_ok = total_warn = total_err = 0
    for title, (ok, warn, err) in sections:
        print(f"\n=== {title} ===")
        for m in ok:
            print(f"  ✅ {m}")
        for m in warn:
            print(f"  ⚠️  {m}")
        for m in err:
            print(f"  ❌ {m}")
        if not (ok or warn or err):
            print("  (tidak ada yang dicek)")
        total_ok += len(ok)
        total_warn += len(warn)
        total_err += len(err)

    print(f"\n=== Ringkasan ===")
    print(f"✅ {total_ok}   ⚠️  {total_warn}   ❌ {total_err}")

    if total_err > 0:
        print("\nAda masalah kategori ❌ — sebaiknya dibereskan dulu.")
        sys.exit(1)
    elif total_warn > 0:
        print("\nTidak ada error fatal, tapi ada beberapa ⚠️ yang perlu ditinjau.")
        sys.exit(0)
    else:
        print("\nSemua bersih.")
        sys.exit(0)


if __name__ == "__main__":
    main()

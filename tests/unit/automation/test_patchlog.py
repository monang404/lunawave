"""
Module: tests.unit.automation.test_patchlog

Purpose:
    Regression tests untuk automation/patchlog.py. Sebelum modul ini punya
    test sama sekali (0 dari 81 file test menyentuh automation/), padahal
    tool ini pernah menyebabkan data-loss nyata di docs/PATCHLOG.md dan
    sekarang jadi dependency context_pack.py/find_owner.py.

Responsibilities:
    - Pastikan parse_entries() tahan terhadap variasi format (manual entry
      tanpa baris kosong presisi, Ringkasan multi-baris) — bug nyata yang
      ditemukan di sesi ini (5 entry hilang diam-diam dari 33).
    - Pastikan verify() mendeteksi entry yang gagal parse.
    - Pastikan penomoran ID berikutnya tidak tabrakan walau ada entry lama
      yang gagal parse.

Depends on:
    - automation.patchlog

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless (tiap test independen, tidak menyentuh docs/PATCHLOG.md asli).
"""

import importlib

import pytest


@pytest.fixture()
def patchlog(monkeypatch, tmp_path):
    """Import automation.patchlog dengan PATCHLOG dialihkan ke file
    sementara, supaya test tidak pernah menyentuh docs/PATCHLOG.md asli."""
    import automation.patchlog as pl

    importlib.reload(pl)
    fake_path = tmp_path / "PATCHLOG.md"
    monkeypatch.setattr(pl, "PATCHLOG", fake_path)
    return pl


CANONICAL_TWO_ENTRIES = """---
latest_patch_id: PATCH-2026-01-01-002
total_entries: 2
---

> **Format:** entri baru wajib diawali ID unik.

## [2026-01-02] Entry kedua

**ID:** `PATCH-2026-01-01-002`

**Tanggal:** 2026-01-02

**Ringkasan:** Deskripsi entry kedua.

**File Terdampak:**

- `b.py`

---

## [2026-01-01] Entry pertama

**ID:** `PATCH-2026-01-01-001`

**Tanggal:** 2026-01-01

**Ringkasan:** Deskripsi entry pertama.

**File Terdampak:**

- `a.py`

---
"""


# Entry manual TANPA baris kosong presisi (persis bug nyata yang ditemukan
# di PATCHLOG.md project: entry 072-068 hilang karena separator "---" tidak
# diikuti baris kosong, dan Ringkasan ditulis di baris berikutnya).
MALFORMED_MANUAL_ENTRY = """---
latest_patch_id: PATCH-2026-01-01-002
total_entries: 2
---

## [2026-01-02] Entry rapi

**ID:** `PATCH-2026-01-01-002`

**Tanggal:** 2026-01-02

**Ringkasan:** Entry yang formatnya benar.

**File Terdampak:**

- `b.py`

---
## [2026-01-01] Entry ditulis manual, format berantakan
**ID:** `PATCH-2026-01-01-001`
**Tanggal:** 2026-01-01
**Ringkasan:**
Baris pertama ringkasan.
Baris kedua ringkasan lanjutan.

**File Terdampak:**
- `a.py` — catatan tambahan setelah backtick

---
"""


class TestParseEntries:
    def test_parses_canonical_format(self, patchlog):
        entries = patchlog.parse_entries(CANONICAL_TWO_ENTRIES)
        ids = [e["id"] for e in entries]
        assert ids == ["PATCH-2026-01-01-002", "PATCH-2026-01-01-001"]
        assert entries[0]["files"] == ["b.py"]
        assert entries[0]["ringkasan"] == "Deskripsi entry kedua."

    def test_parses_malformed_manual_entry_without_blank_lines(self, patchlog):
        """Regresi langsung dari bug yang ditemukan: entry manual tanpa
        baris kosong di sekitar '---' dan dengan Ringkasan multi-baris
        harus TETAP ke-parse, bukan hilang diam-diam."""
        entries = patchlog.parse_entries(MALFORMED_MANUAL_ENTRY)
        ids = {e["id"] for e in entries}
        assert "PATCH-2026-01-01-001" in ids, "entry manual yang malformed hilang dari hasil parse"
        assert "PATCH-2026-01-01-002" in ids

        malformed = next(e for e in entries if e["id"] == "PATCH-2026-01-01-001")
        assert "Baris pertama ringkasan." in malformed["ringkasan"]
        assert "Baris kedua ringkasan lanjutan." in malformed["ringkasan"]
        assert malformed["files"] == ["a.py"]

    def test_ignores_chunks_without_id(self, patchlog):
        text = "Beberapa teks pembuka tanpa ID sama sekali.\n\n---\n\n" + CANONICAL_TWO_ENTRIES
        entries = patchlog.parse_entries(text)
        assert len(entries) == 2


class TestVerify:
    def test_ok_when_all_entries_parse(self, patchlog):
        report = patchlog.verify(CANONICAL_TWO_ENTRIES)
        assert report["ok"] is True
        assert report["unparsed_ids"] == []
        assert report["total_ids_found"] == report["total_parsed"] == 2

    def test_detects_unparsed_entry(self, patchlog):
        # Rusak lebih jauh: hapus baris "**File Terdampak:**" dari entry
        # 001 supaya benar-benar tidak mungkin ke-parse, walau splitter
        # sudah ditoleransi.
        broken = MALFORMED_MANUAL_ENTRY.replace("**File Terdampak:**\n- `a.py`", "")
        report = patchlog.verify(broken)
        assert report["ok"] is False
        assert "PATCH-2026-01-01-001" in report["unparsed_ids"]


class TestAddEntryNumbering:
    def test_next_id_uses_max_existing_sequence_not_parsed_count(self, patchlog, monkeypatch):
        """Bug nyata yang ditemukan: sebelumnya next ID dihitung dari
        `len(parse_entries(...)) + 1`. Kalau parser kehilangan entry
        (skenario di atas), next ID akan TABRAKAN dengan ID yang sudah
        dipakai. Next ID harus selalu > NNN tertinggi yang benar-benar ada
        di file, terlepas dari berapa banyak yang berhasil di-parse penuh.
        """
        # Tulis file dengan 1 entry "rapi" (parseable) dan 1 entry manual
        # rusak yang py punya ID lebih tinggi (073-ish) — meniru kondisi
        # nyata project (id tertinggi ada di entry yang formatnya rusak).
        text = CANONICAL_TWO_ENTRIES.replace(
            "**ID:** `PATCH-2026-01-01-002`", "**ID:** `PATCH-2026-01-01-099`"
        )
        # Buat entry 099 gagal parse penuh (hapus Ringkasan-nya) supaya
        # hanya 1 dari 2 ID yang berhasil di-parse -- persis kondisi bug.
        text = text.replace(
            "**Ringkasan:** Deskripsi entry kedua.\n\n**File Terdampak:**",
            "**File Terdampak:**",
        )
        patchlog.PATCHLOG.write_text(text, encoding="utf-8")

        entries = patchlog.parse_entries(text)
        assert len(entries) == 1, "sanity check: entry 099 memang gagal parse penuh"

        next_id = patchlog._next_id(entries)
        # len(entries) + 1 == 2 -> akan jadi -002 yang TABRAKAN dengan ID
        # yang sudah ada. Next ID yang benar harus > 099.
        seq = int(next_id.rsplit("-", 1)[1])
        assert seq == 100, f"expected seq 100 (max existing + 1), got {seq}"

    def test_add_entry_produces_canonical_parseable_format(self, patchlog):
        patchlog.PATCHLOG.write_text(CANONICAL_TWO_ENTRIES, encoding="utf-8")
        new_id = patchlog.add_entry("Test entry baru", ["c.py", "d.py"])

        text = patchlog.PATCHLOG.read_text(encoding="utf-8")
        entries = patchlog.parse_entries(text)
        ids = [e["id"] for e in entries]
        assert new_id in ids
        newest = next(e for e in entries if e["id"] == new_id)
        assert newest["files"] == ["c.py", "d.py"]

        # add_entry harus tidak merusak frontmatter YAML pembuka.
        assert text.startswith("---\nlatest_patch_id:")

    def test_add_entry_does_not_insert_inside_frontmatter(self, patchlog):
        patchlog.PATCHLOG.write_text(CANONICAL_TWO_ENTRIES, encoding="utf-8")
        patchlog.add_entry("Entry lain", ["e.py"])
        text = patchlog.PATCHLOG.read_text(encoding="utf-8")
        # frontmatter tetap 3 baris (buka --- / 2 field / tutup ---) diikuti
        # blockquote format-notice sebelum entry pertama muncul.
        fm_end = text.index("\n---", 3)
        frontmatter = text[: fm_end + 4]
        assert "**ID:**" not in frontmatter

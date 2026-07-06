# Implementation Plan Index

Tujuan project: Menyelesaikan seluruh temuan dari audit codebase.
Total audit: 15 file. Total finding valid: 241. Total sprint: 7. Total task: 237.

## Workflow AI
1. Baca ROADMAP, cari sprint berstatus ACTIVE.
2. Cari task pertama berstatus TODO di sprint tsb (urut priority P0 → P3).
3. Jika task berstatus BLOCKED-DECISION, jangan dikerjakan — laporkan ke manusia untuk keputusan.
4. Baca audit asli di REPORTS/ hanya jika detail di task belum cukup.
5. Implementasikan sesuai Acceptance Criteria.
6. Validasi sesuai Validation Checklist.
7. Update status task jadi DONE, pindahkan file ke `DONE/`, update baris terkait di `MAPPING.md` dan tambahkan entri di `CHANGELOG.md`.
8. Lanjut ke task berikutnya.

## Normalisasi Priority
| Severity Asli (varian apapun) | Priority Final |
|---|---|
| Critical / 🔴 / berdampak security exploitable / data loss | P0 |
| High / 🟠 | P1 |
| Medium / 🟡 | P2 |
| Low / 🟢 / cosmetic / nice-to-have | P3 |

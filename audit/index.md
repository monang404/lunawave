# AI Agent Workflow Instructions (Entry Point)

Selamat datang! Dokumen ini adalah panduan alur kerja (workflow) utama yang **wajib dibaca pertama kali** oleh AI Agent setiap kali memulai sesi pekerjaan. Alur kerja ini dirancang agar disiplin, terstruktur, dan mudah diaudit.

## 1. Pahami Konteks Proyek (Membaca Referensi)
Sebelum melakukan analisis atau eksekusi apapun, kamu wajib membaca dan memahami dokumen-dokumen berikut:
- `ROADMAP.md`: Untuk memahami arah proyek secara keseluruhan, prioritas saat ini, dan milestone yang sedang berjalan.
- `MAPPING.md`: Untuk memahami struktur direktori, arsitektur, dan peta file/komponen dari proyek ini.
- `Task_execution_rules.md`: **WAJIB DIBACA SEBELUM EKSEKUSI**. Dokumen ini berisi aturan ketat tentang bagaimana setiap task harus dikerjakan, divalidasi, dan didokumentasikan. Prinsip utama: **Satu Task = Satu Unit Pekerjaan**.

## 2. Pilih dan Pahami Task (Status TODO)
- Masuk ke direktori `TASK/`.
- Temukan file task (contoh: `S01-001.md`, `S02-005.md`) yang masih berada di root direktori `TASK/` dan memiliki status **TODO**.
- Baca detail task tersebut untuk memahami:
  - Tujuan dan ruang lingkup (scope) pekerjaan.
  - File apa saja yang mungkin terpengaruh.
  - Kriteria sukses (Success Criteria).
- Rencanakan implementasi berdasarkan instruksi di task dan arsitektur di `MAPPING.md`.

## 3. Eksekusi dan Implementasi
- Lakukan modifikasi kode sesuai dengan deskripsi task. Kamu boleh menggabungkan implementasi dari beberapa task sekaligus asalkan relevan, namun **administrasi tetap dilakukan satu per satu per task**.
- Pastikan hanya mengerjakan scope yang ada di dalam task tersebut (Scope Discipline).
- Setelah kode diubah, lakukan **Test** dan **Build** sesuai dengan kriteria yang ditentukan di task. Pastikan semuanya lolos sebelum lanjut ke tahap penyelesaian.

## 4. Administrasi dan Penyelesaian (Post-Execution)
Setiap task yang telah selesai diimplementasi dan dites dengan sukses **wajib** diikuti dengan langkah-langkah administrasi berikut secara **satu per satu per task**:

1. **Update Data Task**:
   - Buka file task yang bersangkutan.
   - Ubah statusnya menjadi **DONE**.
   - Perbarui bagian hasil eksekusi, pastikan checklist Success Criteria tercentang.
2. **Update Changelog**:
   - Buka `LOG/CHANGELOG.md`.
   - Tambahkan entry khusus untuk task yang baru saja diselesaikan. Format changelog harus menjelaskan:
     - Nomor Task (contoh: S01-001)
     - Apa yang dilakukan / diimplementasikan.
     - File apa saja yang diubah, ditambah, atau dihapus.
     - Status testing (misal: "Sudah di-test dan lolos validasi lokal").
3. **Pindahkan File Task (Move to DONE)**:
   - Pindahkan file task tersebut dari root direktori `TASK/` ke dalam folder sprint yang sesuai di dalam `TASK/DONE/` (contoh: dipindahkan ke `TASK/DONE/Sprint 1/`).
4. **Update Dokumen Lainnya**:
   - Update `MAPPING.md` jika implementasi task ini menambah file baru atau mengubah fungsi/arsitektur utama.
   - Update `ROADMAP.md` jika task tersebut menandai selesainya sebuah milestone atau fase tertentu.

---

**Perhatian**: Jangan pernah memindahkan file task ke direktori `DONE` sebelum kode selesai dites, validasi lulus, dan changelog beserta seluruh dokumentasinya selesai diperbarui. Disiplin adalah kunci.

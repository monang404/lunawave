# TASK EXECUTION RULES

## Purpose

Dokumen ini mengatur disiplin AI Agent dalam mengerjakan, mencatat, memvalidasi, dan menyelesaikan setiap task.

Target utama adalah memastikan setiap task memiliki riwayat yang lengkap, mudah diaudit, dan terdokumentasi secara konsisten.

---

# Core Principle

**Satu Task = Satu Unit Pekerjaan = Satu Riwayat = Satu Validasi = Satu Completion Report**

Walaupun implementasi dapat menyelesaikan beberapa task sekaligus, setiap task tetap harus diperlakukan sebagai pekerjaan yang berdiri sendiri.

Jangan pernah menggabungkan dokumentasi beberapa task menjadi satu.

---

# Execution Workflow

Untuk setiap task lakukan urutan berikut:

1. Read Task
2. Understand References
3. Analyze Impact
4. Plan Implementation
5. Implement
6. Test
7. Validate Success Criteria
8. Update Documentation
9. Complete Task
10. Move to DONE

Jangan melompati tahapan.

---

# Parallel Execution

AI diperbolehkan:

* membaca banyak task
* menganalisis banyak task
* membuat satu implementasi yang menyelesaikan beberapa task

Namun administrasi tetap dilakukan satu task demi satu task.

Contoh:

Implementasi:

S1-001
S1-002
S1-003

boleh dilakukan bersamaan.

Tetapi setelah implementasi selesai, proses berikut wajib dilakukan secara berurutan:

S1-001

* Validasi
* Update Changelog
* Update Mapping
* Update Roadmap
* Completion Report
* Move to DONE

baru lanjut ke

S1-002

lalu

S1-003

---

# Individual Validation

Setiap task wajib memiliki:

* Build Result
* Test Result
* Success Criteria
* Documentation Update
* Completion Status

Tidak boleh menggunakan validasi gabungan.

SALAH

"Semua task S1-001 sampai S1-010 berhasil."

BENAR

S1-001

✓ Build

✓ Test

✓ Done

---

S1-002

✓ Build

✓ Test

✓ Done

---

# Individual Changelog

Setiap task menghasilkan entry changelog sendiri.

Jangan membuat changelog gabungan.

SALAH

Completed:

S1-001 sampai S1-010

BENAR

S1-001

Added Login Endpoint

---

S1-002

Added JWT Validation

---

S1-003

Added Unit Test

---

# Individual Completion Report

Setiap task wajib memiliki ringkasan sendiri.

Minimal berisi:

Task ID

Objective

Summary

Files Modified

Validation Result

Documentation Updated

Status

Jangan menggabungkan beberapa task dalam satu laporan.

---

# Success Criteria

Task hanya boleh selesai apabila:

✓ seluruh checklist selesai

✓ seluruh test berhasil

✓ build berhasil

✓ lint berhasil

✓ tidak ada regression

✓ dokumentasi diperbarui

✓ changelog diperbarui

✓ roadmap diperbarui (jika diperlukan)

✓ mapping diperbarui (jika diperlukan)

Apabila satu saja gagal, status tetap belum selesai.

---

# Documentation Update Order

Untuk setiap task lakukan:

1. Update Changelog

2. Update Mapping

3. Update Roadmap

4. Update Knowledge (jika ada)

5. Update Decisions (jika ada)

Setelah itu baru:

Update Status = DONE

---

# Move To DONE

Task hanya boleh dipindahkan ke folder DONE apabila:

* Success Criteria selesai
* Dokumentasi selesai
* Validasi selesai

Tidak boleh memindahkan task terlebih dahulu lalu melengkapi dokumentasi.

---

# Dependency

Apabila task memiliki dependency:

Jangan mengubah status menjadi DONE sebelum dependency selesai.

Jika dependency belum selesai:

Status = BLOCKED

sertakan alasan.

---

# Scope Discipline

Kerjakan hanya ruang lingkup yang terdapat pada task.

Jangan:

* menambah fitur baru
* melakukan refactor besar
* mengubah requirement
* mengubah arsitektur

kecuali memang diminta.

---

# Documentation Discipline

Dokumentasi harus selalu mencerminkan kondisi implementasi terbaru.

Setiap perubahan implementasi yang memengaruhi dokumentasi wajib diperbarui.

Tidak boleh ada implementasi tanpa dokumentasi.

---

# Audit Trail

Setiap task harus dapat diaudit secara independen.

Seseorang harus dapat membuka satu task dan mengetahui:

* apa yang dikerjakan
* mengapa dikerjakan
* file apa yang berubah
* bagaimana hasil validasinya
* kapan selesai
* dokumentasi apa yang berubah

tanpa harus membaca task lain.

---

# Consistency Rules

Gunakan format yang sama untuk seluruh task.

Jangan mengubah struktur task.

Jangan mengubah format changelog.

Jangan mengubah format roadmap.

Jangan mengubah format mapping.

Konsistensi lebih penting daripada variasi.

---

# Error Handling

Apabila implementasi gagal:

Jangan memindahkan task.

Jangan mencentang Success Criteria.

Catat:

* penyebab
* blocker
* solusi yang disarankan

Ubah status menjadi BLOCKED apabila diperlukan.

---

# Golden Rules

Selalu:

✓ Satu Task = Satu Riwayat

✓ Satu Task = Satu Validasi

✓ Satu Task = Satu Changelog

✓ Satu Task = Satu Completion Report

✓ Satu Task = Satu Status

✓ Satu Task = Satu Audit Trail

Tidak pernah:

✗ Menggabungkan beberapa task menjadi satu laporan.

✗ Menggabungkan beberapa task menjadi satu changelog.

✗ Menganggap task selesai hanya karena implementasinya sama.

✗ Menandai DONE tanpa validasi.

✗ Memindahkan task sebelum seluruh dokumentasi selesai.

Setiap task harus dapat berdiri sendiri dan dapat diaudit secara independen tanpa bergantung pada task lain.

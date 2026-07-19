---
title: Task Breakdown — Quick Search Discover & Redesain Login
created: 2026-07-19
status: final — keputusan desain sudah ditetapkan, siap eksekusi
---

# task_breakdown.md

Panduan eksekusi bertahap untuk dua fitur:
- **Fitur A — Quick Search di tab Discover** (pencarian atas data lokal: judul/artis, dengan filter kategori & dekade)
- **Fitur B — Redesain sistem login** (halaman Initial Setup + kredensial admin dinamis di SQLite, menggantikan auto-generate password file)

Dokumen ini dipecah jadi task-task kecil, diurutkan berdasarkan dependency, supaya tiap task bisa dikerjakan, divalidasi, dan di-commit secara independen. Setiap task mengikuti alur kerja wajib di `AI_CONTEXT.md` (baca dulu file itu jika belum).

Semua keputusan desain yang sebelumnya terbuka sudah **ditetapkan** di §0, dengan pilihan yang paling konsisten dengan arsitektur, pola, dan prinsip yang sudah dianut project saat ini (bukan menambah pola baru). Task-task di bawah langsung mengasumsikan keputusan ini — tidak ada lagi task yang menunggu input pemilik project sebelum bisa dikerjakan.

## Cara pakai dokumen ini

- Checkbox `[ ]` di judul task = belum dikerjakan. Centang manual saat task selesai & tervalidasi.
- 🔒 = **governance-locked** — file ini terkunci di `AI_CONTEXT.md` dan **butuh izin eksplisit dari pemilik project tepat sebelum task itu dikerjakan**, terpisah dari izin mengerjakan task itu sendiri. Ini satu-satunya jenis persetujuan manusia yang masih diperlukan di dokumen ini.
- Setiap task mencantumkan: **Depends on**, **File**, **Langkah kerja**, **Automation**, **Definition of Done**.
- Urutan task = urutan dependency, bukan sekadar saran — jangan lompat ke task governance-locked sebelum task non-locked di depannya selesai & tervalidasi doctor.py.
- Satu task = idealnya satu commit = satu entry baru di `docs/PATCHLOG.md` (format `PATCH-YYYY-MM-DD-NNN`, prepend, jangan digabung beberapa task jadi satu entry).

---

## §0. Keputusan Desain (final)

Lima titik yang sebelumnya punya beberapa opsi, sudah ditetapkan ke opsi yang paling konsisten dengan sistem yang sudah ada — dipilih untuk menghindari pola baru, kolom skema baru, atau sumber kebenaran ganda yang tidak perlu. Task di §2/§3 langsung mengimplementasikan pilihan ini, tanpa cabang alternatif.

| # | Titik keputusan | Ditetapkan | Alasan konsistensi dengan sistem existing |
|---|---|---|---|
| K1 | Cakupan filter **Genre** di Quick Search | Diturunkan jadi filter kategori **Solo/Band** yang sudah ada (`#kategori-toggle`) | Genre asli hanya ada di level artis (`artists` → `artist_genres`), bukan di `tracks`; join by nama artis tidak reliable (bukan foreign key). Kategori Solo/Band sudah difilter dengan pola yang sama di `filter-bar` Discover — tidak perlu kolom baru atau string-matching baru. |
| K2 | Cakupan filter **Tahun** di Quick Search | Diturunkan jadi filter **dekade** yang sudah ada (`#decade-dropdown-container`) | Tidak ada kolom tahun rilis di skema manapun untuk track (`artists.tahun_aktif` di level artis, teks bebas, bukan angka). Filter dekade sudah persis ada di Discover dan sudah "memutuskan" granularitas ini sebagai yang cocok untuk konteks ini. |
| K3 | Strategi **migrasi kredensial lama** saat cut-over login | **Tidak migrasi otomatis** — user existing wajib lewat Initial Setup ulang saat upgrade | Ada dua file password berbeda di lapangan (`cache/admin_password.txt`, `instance/admin_password.txt`) yang tidak sinkron satu sama lain; migrasi otomatis harus menebak salah satu sebagai sumber benar, risiko salah pilih lebih besar dari biaya re-setup sekali. Sejalan dengan prinsip "hindari perubahan yang tidak diperlukan" yang sudah dipegang project. |
| K4 | Nasib env var override (`LUNAWAVE_ADMIN_PASS`/`YTGUI_ADMIN_PASS`) | **Dipertahankan** sebagai jalur override eksplisit, terpisah dari auto-generate yang dihapus | Dibutuhkan untuk deployment non-interaktif (CI, provisioning otomatis); menghapusnya total tidak diminta dan justru mengurangi fleksibilitas config yang sudah ada tanpa manfaat keamanan tambahan, karena override tetap butuh akses env/config secara eksplisit. |
| K5 | Peran tombol "Reset Password" launcher GUI pasca-konsolidasi | **Redirect** ke halaman web Initial-Setup-ulang/login | Menghindari launcher desktop punya mekanisme auth sendiri yang terpisah dari sumber kebenaran (`admin_account` di SQLite, dikelola lewat web) — ini persis akar masalah Temuan C (dua sistem password tidak sinkron) yang sedang ditutup oleh redesain ini. Satu sumber kebenaran, satu jalur perubahan. |

> Kalau di kemudian hari kebutuhan berubah (mis. library membesar signifikan dan genre/tahun presisi jadi penting, atau muncul kebutuhan migrasi otomatis lintas-instalasi), itu jadi sprint/keputusan produk terpisah — bukan mengubah task-task di bawah secara diam-diam.

---

## §1. Orientasi (jalankan sekali di awal sesi kerja, sebelum task apa pun)

### [ ] T0.1 — Baca governance & regenerate peta repo
**Depends on:** —
**File:** tidak ada perubahan file kode
**Langkah kerja:**
1. Baca `AI_CONTEXT.md` (aturan file terkunci, batasan teknis, alur kerja wajib).
2. Baca `docs/STATUS.md` khusus baris yang menyebut `server/handlers/websocket.py`, `web/static/index.html`, `persistence/discover_repo.py`, `server/handlers/auth.py`, `config.py`, `launcher/`.
3. Baca 2–3 entry terakhir `docs/PATCHLOG.md` untuk konteks perubahan terbaru yang menyentuh area yang sama.
**Automation:**
```bash
python automation/repo_map.py
cat docs/DEPENDENCY_GRAPH.json | head -100
python automation/doctor.py
```
**Definition of Done:** `doctor.py` menunjukkan baseline PASS/WARN yang dipahami (dicatat, bukan diperbaiki di task ini — task ini murni orientasi), `DEPENDENCY_GRAPH.json` sudah ter-regenerate dan up to date.

### [ ] T0.2 — Cari owner file-file kunci
**Depends on:** T0.1
**Langkah kerja:** jalankan `find_owner.py` untuk tiap target di bawah, catat callers/dependencies/status sebelum menyentuh kode apa pun.
**Automation:**
```bash
python automation/find_owner.py persistence/discover_repo.py
python automation/find_owner.py server/handlers/ws_discovery.py
python automation/find_owner.py server/handlers/websocket.py
python automation/find_owner.py server/handlers/auth.py
python automation/find_owner.py config.py
python automation/find_owner.py launcher/auth_service.py
python automation/context_pack.py server/handlers/auth.py
```
**Definition of Done:** hasil owner/dependency untuk ketujuh target sudah dibaca dan dipahami sebelum mengerjakan task implementasi apa pun di §2/§3.

---

## §2. Fitur A — Quick Search Discover

### Tahap A1 — Backend (tidak menyentuh file governance-locked)

#### [ ] T-A1 — Method `search_tracks` di repository
**Depends on:** T0.2
**File:** `persistence/discover_repo.py` (modifikasi — tambah method baru)
**Langkah kerja:**
1. Tambah method `search_tracks(query: str, kategori: str | None = None, decade: str | None = None)` yang query `LIKE` ke `title`/`artist` pada tabel `tracks`, mengikuti gaya query method lain di file yang sama (raw query, tanpa logika skor/ranking di layer ini).
2. Filter `kategori` mengacu langsung ke kolom kategori Solo/Band yang sudah dipakai `filter-bar` Discover (K1) — **tidak** ada join ke `artists`/`artist_genres`.
3. Filter `decade` mengacu ke pola dekade yang sudah dipakai `#decade-dropdown-container` (K2) — **tidak** ada kolom tahun baru di skema.
4. Tidak menambah kolom skema baru di task ini.
**Automation:**
```bash
python automation/find_owner.py discover_repo.py   # ulang, pastikan tidak ada perubahan mengejutkan sejak T0.2
```
**Definition of Done:** method baru ada, tidak mengubah behavior method lain di file yang sama, filter kategori/dekade konsisten dengan definisi yang sudah dipakai `filter-bar` Discover (bukan definisi baru).

#### [ ] T-A2 — Unit test untuk `search_tracks`
**Depends on:** T-A1
**File:** `tests/unit/persistence/test_discover_repo_search.py` (baru)
**Langkah kerja:** test minimal: query cocok judul, query cocok artis, query tidak ada hasil, filter kategori Solo/Band aktif, filter dekade aktif, query kosong/whitespace tidak crash.
**Automation:**
```bash
python automation/test_locator.py discover_repo
pytest tests/unit/persistence/test_discover_repo_search.py -q
```
**Definition of Done:** semua test baru hijau; test suite lama tidak regresi (jalankan test existing di folder yang sama).

#### [ ] T-A3 — Handler routing `discover_search` (belum reachable dari client)
**Depends on:** T-A1
**File:** `server/handlers/ws_discovery.py` (modifikasi — tambah branch baru)
**Langkah kerja:** tambah `elif action == "discover_search":` yang memanggil `search_tracks(...)` dan mengembalikan payload dengan bentuk serupa hasil `"search"`/`"discover"` yang sudah ada (agar frontend bisa reuse renderer). Nama action **harus** `discover_search`, bukan reuse `"search"` (yang artinya pencarian YouTube live) — jangan tertukar makna.
**Automation:**
```bash
python automation/architecture_lint.py
```
**Definition of Done:** branch baru ada dan bisa dites manual lewat WebSocket console dengan mengirim `{"action":"discover_search","query":"..."}` **setelah** T-A4 selesai (karena sebelum T-A4, action ini belum lolos whitelist `DISCOVERY_CMDS`, jadi test end-to-end baru bisa dilakukan setelah Tahap A2). Untuk task ini cukup validasi lewat unit test/mocking bahwa branch terpanggil dengan benar.

> **Checkpoint sebelum lanjut ke Tahap A2:** jalankan `python automation/doctor.py` — harus tetap PASS/WARN yang sama seperti baseline T0.1, tidak ada FAIL baru. Prepend entry `docs/PATCHLOG.md` untuk T-A1–T-A3 (boleh 1 entry gabungan karena satu unit kerja "backend Quick Search tanpa UI", sesuai preseden dokumentasi proyek — beda dengan tahap governance-locked di bawah yang **wajib** entry terpisah).

### Tahap A2 — Registrasi command 🔒

#### [ ] T-A4 — Tambah `discover_search` ke whitelist 🔒
**Depends on:** T-A3, **izin eksplisit dari pemilik project untuk menyentuh `server/handlers/websocket.py`** (minta persis sebelum task ini, jangan diam-diam disisipkan di task lain)
**File:** `server/handlers/websocket.py` 🔒 (modifikasi 1 baris — tambah `"discover_search"` ke `DISCOVERY_CMDS`)
**Langkah kerja:** tambah satu string ke set `DISCOVERY_CMDS` yang sudah ada di baris tersebut. Tidak ada perubahan lain di file ini pada task ini.
**Automation:**
```bash
python automation/find_owner.py websocket.py
python automation/doctor.py --strict
```
**Definition of Done:** command lama (`search`, `discover`, `get_artist_detail`) tetap berfungsi (regresi test WebSocket), `discover_search` sekarang reachable dari client dan bisa dites end-to-end via WebSocket console.

---

### Tahap A3 — UI Quick Search Discover 🔒

#### [ ] T-A5 — Markup search bar & filter row di Discover 🔒
**Depends on:** T-A4, **izin eksplisit terpisah untuk menyentuh `web/static/index.html`**
**File:** `web/static/index.html` 🔒 (modifikasi — tambah markup baru di section `#tab-discover`, sebelum `.taste-block`)
**Langkah kerja:**
1. Tambah search bar dengan class baru (bukan reuse langsung `.search-wrap` tanpa scoping) — mis. `.discover-search-wrap`, agar CSS tidak saling memengaruhi dengan tab Search global.
2. Tambah filter row (reuse `.segmented` untuk kategori Solo/Band + `.custom-dropdown` untuk dekade — persis komponen yang sudah ada di `filter-bar` Discover, sesuai K1/K2) yang **hanya muncul saat query aktif** (progressive disclosure — pola yang sudah dipakai proyek di `discover-tab.js`).
3. Jangan ubah struktur section Discover yang sudah ada — tambahan harus terisolasi lewat id/class baru.
**Automation:**
```bash
python automation/verify_structure.py --verbose   # cek ambang ukuran file index.html
```
**Definition of Done:** markup baru ada, tidak mengubah rendering elemen Discover lain yang sudah ada (screenshot before/after manual check).

#### [ ] T-A6 — CSS Quick Search Discover
**Depends on:** T-A5
**File:** `web/static/css/components/discover-search.css` (baru) — pisahkan dari `discover-cards.css` supaya file itu tidak makin gemuk (lihat ambang ukuran di `STATUS.md`)
**Langkah kerja:** styling search bar + filter row, ikuti token spacing `--s*` project-wide, tanpa breakpoint baru (mobile/tablet sama, desktop reuse layout grid yang sudah ada).
**Automation:**
```bash
python automation/verify_structure.py
```
**Definition of Done:** tampil benar di 3 breakpoint (mobile/tablet/desktop), tidak ada warning ukuran file baru dari `verify_structure.py`.

#### [ ] T-A7 — Event handling & debounce
**Depends on:** T-A5
**File:** `web/static/js/events/discover-search-events.js` (baru) — mirror pola `search-input-events.js` (debounce 500ms, tombol clear/reset)
**Langkah kerja:** wiring input → debounce → `wsSend("discover_search", {query, kategori, decade})`, toggle tampilan filter row saat query aktif/kosong.
**Automation:** —
**Definition of Done:** mengetik di search bar memicu request `discover_search` setelah 500ms idle, tombol clear mengembalikan ke state awal.

#### [ ] T-A8 — Render hasil pencarian Discover
**Depends on:** T-A7
**File:** `web/static/js/render/discover-search.js` (baru) — mirror ringan `render/search.js`, ditambah kemampuan toggle mode "rekomendasi" vs "hasil pencarian"
**Langkah kerja:** render state Initial/Loading/Empty(query dikosongkan → kembali ke rekomendasi normal)/No result/Error sesuai pola yang sudah ada di `render/search.js` dan `utils/toast.js`. Reuse `.sr-item` untuk daftar hasil di semua breakpoint (tidak perlu grid card khusus desktop).
**Automation:** —
**Definition of Done:** kelima state tampil benar; rekomendasi personalisasi (Untuk Kamu, dst.) tetap utuh dan kembali tampil begitu query dikosongkan, tanpa reload halaman.

#### [ ] T-A9 — Registrasi elemen DOM baru
**Depends on:** T-A5
**File:** `web/static/js/main.js`, `web/static/js/dom.js` (modifikasi — tambah referensi elemen DOM baru, ikuti pola registrasi `dom.*` yang sudah ada)
**Automation:** —
**Definition of Done:** elemen baru terdaftar dan dipakai konsisten oleh T-A7/T-A8 (tidak ada `document.querySelector` liar di luar `dom.js`).

> **Checkpoint sebelum lanjut ke Fitur B:** jalankan `python automation/doctor.py`, `generate_file_index.py`, `generate_report.py`. Prepend entry `docs/PATCHLOG.md` (task governance-locked T-A4 dan T-A5 **masing-masing entry sendiri**; T-A6–T-A9 boleh digabung satu entry "UI Quick Search Discover"). Update `docs/backend/persistence.md`, `docs/backend/api.md`, `docs/STATUS.md` baris terkait.

---

## §3. Fitur B — Redesain Login

> Catatan urutan: Fitur B tidak depend pada Fitur A — keduanya bisa dikerjakan paralel/independen kalau perlu. Urutan di bawah adalah urutan internal Fitur B saja.

### Tahap B1 — Skema & repository akun admin (tidak governance-locked)

#### [ ] T-B1 — Tabel `admin_account`
**Depends on:** T0.2
**File:** `persistence/schema.sql` (modifikasi — tambah `CREATE TABLE IF NOT EXISTS admin_account (username TEXT UNIQUE, password_hash TEXT, created_at INTEGER)`)
**Langkah kerja:** ikuti pola `ALTER TABLE`/`CREATE TABLE IF NOT EXISTS` bertahap yang sudah dianut proyek (lihat pola di `persistence/__init__.py`), pastikan DB lama tetap bisa dibuka tanpa error.
**Automation:**
```bash
python automation/find_owner.py persistence/schema.sql
```
**Definition of Done:** migrasi backward-compatible tervalidasi — buka DB lama (tanpa tabel ini) dan pastikan startup tidak error, tabel baru otomatis terbuat.

#### [ ] T-B2 — Repository `admin_account_repo.py`
**Depends on:** T-B1
**File:** `persistence/admin_account_repo.py` (baru) — mirror pola persis `session_repo.py`
**Langkah kerja:** method minimal: `get_admin_account()`, `create_admin_account(username, password_hash)`, `admin_account_exists()`. Tidak ada logika hashing di layer ini (hashing tetap di `core/security.py`).
**Automation:**
```bash
python automation/find_owner.py session_repo.py   # pola referensi
```
**Definition of Done:** repository baru lulus unit test dasar (lihat T-B3).

#### [ ] T-B3 — Unit test repository baru
**Depends on:** T-B2
**File:** `tests/unit/persistence/test_admin_account_repo.py` (baru)
**Langkah kerja:** test create, get saat kosong, get setelah create, constraint `UNIQUE username` (dua create gagal pada create kedua).
**Automation:**
```bash
pytest tests/unit/persistence/test_admin_account_repo.py -q
```
**Definition of Done:** semua test hijau, termasuk skenario race `UNIQUE` constraint (dua insert konkuren → satu gagal, bukan dua-duanya sukses).

#### [ ] T-B4 — Daftarkan repo baru ke container
**Depends on:** T-B2
**File:** `persistence/__init__.py` (modifikasi — tambah `repos.admin_account`, mengikuti pola facade tipis yang sudah ada seperti `repos.discover`)
**Automation:**
```bash
python automation/doctor.py
```
**Definition of Done:** `repos.admin_account` bisa diakses dari module lain tanpa error import; `architecture_lint.py` tetap PASS (import boundary tidak dilanggar).

> **Checkpoint:** prepend 1 entry PATCHLOG untuk T-B1–T-B4 ("infrastruktur penyimpanan admin_account, belum dipakai auth flow").

### Tahap B2 — Handler setup (belum reachable dari client)

#### [ ] T-B5 — Handler `setup_admin`
**Depends on:** T-B4
**File:** `server/handlers/setup.py` (baru)
**Langkah kerja:**
1. Validasi input: username wajib diisi, password minimum length eksplisit (definisikan angka konkret, bukan aturan kompleksitas karakter), confirm password **tidak** dikirim ke server (validasi confirm murni di client, T-B12).
2. Hash pakai `core/security.py` yang sudah ada (jangan ubah/ganti implementasi hashing).
3. Simpan lewat `repos.admin_account.create_admin_account(...)`.
4. Tangani race condition: dua submit bersamaan → submit kedua gagal dengan pesan jelas ("akun admin sudah dibuat, silakan refresh"), bukan overwrite diam-diam.
5. Tambahkan endpoint/handler `GET /api/setup-required` (atau action WS setara) yang mengecek `repos.admin_account.admin_account_exists()` — dipakai frontend untuk memutuskan tampilkan `#portal-screen` vs `#setup-screen`.
6. Terapkan rate limiting yang sama (5x/5menit per IP) seperti `handle_auth`, supaya endpoint setup tidak jadi celah baru yang belum dilindungi.
**Automation:**
```bash
python automation/find_owner.py auth.py   # pola referensi rate limiting & validasi
```
**Definition of Done:** handler bisa dites lewat unit test (mock repo) untuk skenario: sukses, username kosong, password terlalu pendek, submit ganda (race), rate limit terlampaui.

#### [ ] T-B6 — Tidak ada migrasi otomatis kredensial lama (K3)
**Depends on:** T-B5
**File:** `docs/adr/` atau `docs/security/threat_model.md` (dokumentasi keputusan, tidak ada perubahan kode runtime)
**Langkah kerja:**
1. Startup **tidak** mencoba membaca/migrasikan `cache/admin_password.txt` atau `instance/admin_password.txt` ke `admin_account`. Instalasi lama akan melihat halaman Initial Setup saat pertama kali menjalankan versi baru, persis seperti instalasi baru.
2. Tulis catatan eksplisit (di ADR baru, lihat T-B18, atau `docs/security/threat_model.md`) bahwa upgrade akan "logout paksa" dan mewajibkan Initial Setup ulang — ini keputusan sengaja, sertakan draft satu paragraf untuk changelog/README yang menjelaskan ini ke user.
3. Env var override `LUNAWAVE_ADMIN_PASS`/`YTGUI_ADMIN_PASS` (K4) tetap tersedia sebagai jalur eksplisit terpisah untuk deployment non-interaktif — dikerjakan di T-B14, dicatat di sini agar tidak tertukar dengan "migrasi otomatis" yang sengaja tidak dibuat.
**Automation:**
```bash
python automation/impact.py persistence/admin_account_repo.py   # cek siapa lagi yang perlu tahu perubahan ini
```
**Definition of Done:** perilaku startup untuk instalasi baru dan instalasi lama (dengan atau tanpa file password lama) **identik** — keduanya diarahkan ke Initial Setup; catatan changelog/ADR draft siap dipakai di T-B18/T-B19.

#### [ ] T-B7 — Fallback kegagalan setup
**Depends on:** T-B5, T-B6
**File:** `server/handlers/setup.py` — tambah error handling
**Langkah kerja:** pastikan kegagalan (DB corrupt, disk penuh saat submit form) menghasilkan halaman error jelas ("Gagal menyimpan akun admin, cek log"), server tetap bisa start, **tidak pernah** membuat akun kosong yang bisa login tanpa password.
**Automation:**
```bash
python automation/verify_security.py --verbose
```
**Definition of Done:** simulasi kegagalan (mis. mock write error) tidak menghasilkan state login-tanpa-password.

> **Checkpoint:** prepend entry PATCHLOG untuk T-B5–T-B7 ("handler setup_admin, belum reachable dari client").

### Tahap B3 — Registrasi command setup 🔒

#### [ ] T-B8 — Routing `setup_admin` di whitelist 🔒
**Depends on:** T-B7, **izin eksplisit terpisah untuk menyentuh `server/handlers/websocket.py`** (izin kedua, terpisah dari izin T-A4 meskipun file sama — minta ulang tepat sebelum task ini)
**File:** `server/handlers/websocket.py` 🔒 (modifikasi — tambah routing action `setup_admin`, dan/atau daftarkan endpoint HTTP `/api/setup-required` di tempat routing HTTP proyek)
**Automation:**
```bash
python automation/doctor.py --strict
```
**Definition of Done:** `setup_admin` reachable dari client, command lama (termasuk `discover_search` dari Fitur A jika sudah masuk) tetap berfungsi — regresi test WebSocket lengkap.

### Tahap B4 — UI Initial Setup 🔒

#### [ ] T-B9 — Screen `#setup-screen` 🔒
**Depends on:** T-B8, **izin eksplisit terpisah untuk menyentuh `web/static/index.html`** (izin kedua untuk file ini, terpisah dari T-A5)
**File:** `web/static/index.html` 🔒 (modifikasi — tambah `#setup-screen`, reuse struktur `.portal-card`/`.portal-title` dari `#portal-screen` yang sudah ada, tambah field Confirm Password + area pesan validasi)
**Automation:**
```bash
python automation/verify_structure.py --verbose
```
**Definition of Done:** markup baru tidak mengubah `#portal-screen` yang sudah ada.

#### [ ] T-B10 — CSS field Confirm Password
**Depends on:** T-B9
**File:** `web/static/css/portal.css` (modifikasi — perluasan minor)
**Definition of Done:** tampil konsisten dengan `#portal-screen` yang sudah ada, di 3 breakpoint.

#### [ ] T-B11 — Wiring frontend: setup vs login
**Depends on:** T-B9
**File:** modul JS auth/portal yang relevan (telusuri nama file persis via `find_owner.py` saat eksekusi — kemungkinan di `services/auth.js` atau file baru di `events/`)
**Langkah kerja:** panggil `/api/setup-required` (atau action WS setara dari T-B5) saat load, tampilkan `#setup-screen` atau `#portal-screen` sesuai hasil — jangan ditebak murni di client tanpa cek server.
**Automation:**
```bash
python automation/find_owner.py auth.js
```
**Definition of Done:** instalasi baru (folder data kosong) → muncul Initial Setup; instalasi existing dengan akun sudah ada → langsung muncul Login.

#### [ ] T-B12 — Validasi client-side Confirm Password
**Depends on:** T-B9
**File:** modul JS yang sama dengan T-B11
**Langkah kerja:** tombol submit disabled sampai password & confirm sama; **jangan** kirim field confirm ke server.
**Definition of Done:** test manual: password ≠ confirm → submit disabled + pesan jelas; password = confirm → submit aktif.

> **Checkpoint akhir Tahap B4:** test manual end-to-end penuh — instalasi baru (folder data kosong) → Initial Setup muncul → submit → redirect ke Login → login berhasil dengan kredensial baru. Prepend entry PATCHLOG untuk T-B9 (sendiri), T-B10–T-B12 boleh digabung.

### Tahap B5 — Cut-over (risiko tinggi, hanya setelah B4 tervalidasi penuh)

#### [ ] T-B13 — `handle_auth` baca dari `admin_account_repo`
**Depends on:** T-B4, T-B9–T-B12 tervalidasi penuh, konfirmasi eksplisit pemilik project bahwa Tahap B4 sudah dianggap final
**File:** `server/handlers/auth.py` (modifikasi — ganti sumber kredensial dari `config.ADMIN_USERNAME`/`config.ADMIN_PASSWORD` ke query `admin_account_repo`)
**Langkah kerja:** pertahankan `core/security.py` (hashing), `sessions`/`SessionRepository`, rate limiting 5x/5menit apa adanya — hanya ganti sumber baca kredensial. Pertahankan pola constant-time comparison yang sudah ada (`PATCH-2026-07-16-001`, cek username vs password tidak lagi bocor lewat timing).
**Automation:**
```bash
python automation/find_owner.py auth.py
python automation/impact.py server/handlers/auth.py
```
**Definition of Done:** regresi penuh hijau untuk kedua skenario yang sekarang identik per K3 — instalasi baru dan instalasi lama (dengan/tanpa file password lama) sama-sama diarahkan ke Initial Setup lalu login berhasil.

#### [ ] T-B14 — Hapus mekanisme auto-generate di `config.py`, pertahankan override eksplisit (K4)
**Depends on:** T-B13
**File:** `config.py` (modifikasi — hapus blok `IS_PASSWORD_AUTO_GENERATED`, baca/tulis `cache/admin_password.txt`, print banner password)
**Langkah kerja:** pertahankan jalur `LUNAWAVE_ADMIN_PASS`/`YTGUI_ADMIN_PASS` sebagai override eksplisit untuk deployment non-interaktif (K4), tapi pastikan jalurnya jelas terpisah dari kode auto-generate yang dihapus — bukan jalur default, hanya dipakai bila env var itu di-set.
**Automation:**
```bash
python automation/impact.py config.py
```
**Definition of Done:** server start tidak lagi menulis file password baru; override via env var tetap berfungsi dan terdokumentasi sebagai jalur eksplisit non-default.

#### [ ] T-B15 — Bersihkan `config_security.py` & `main.py`
**Depends on:** T-B14
**File:** `config_security.py` (kemungkinan dihapus seluruhnya — cek dulu tidak ada konsumen lain lewat `find_owner.py`), `main.py` (hapus print banner `"PASSWORD ADMIN GENERATED"`)
**Automation:**
```bash
python automation/find_owner.py config_security.py
python automation/impact.py config_security.py
python automation/doctor.py --strict
```
**Definition of Done:** tidak ada import yang patah setelah file dihapus; `doctor.py --strict` PASS.

> **Checkpoint wajib sebelum Tahap B6:** jalankan regression penuh (gaya 8-phase yang sudah pernah dipakai proyek untuk v1.0.0: Regression, E2E, Recovery, dst.), fokus 2 skenario instalasi (baru & lama — kini berperilaku sama per K3). Prepend entry PATCHLOG terpisah untuk masing-masing T-B13/T-B14/T-B15 (ini tahap risiko tinggi, jejak audit granular penting).

### Tahap B6 — Konsolidasi launcher

#### [ ] T-B16 — Rombak `launcher/auth_service.py` & `auth_panel.py`, tombol Reset Password redirect ke web (K5)
**Depends on:** T-B13 (server harus sudah baca dari `admin_account_repo` sebelum launcher diarahkan ke sumber itu)
**File:** `launcher/auth_service.py`, `launcher/gui/auth_panel.py` (modifikasi — hilangkan mekanisme password file terpisah `instance/admin_password.txt`)
**Langkah kerja:** tombol "Reset Password" di GUI diubah jadi redirect ke halaman web (Initial Setup ulang / Login), bukan lagi menulis file lokal yang server tidak pernah baca. Launcher tidak lagi punya mekanisme auth sendiri.
**Automation:**
```bash
python automation/find_owner.py launcher/auth_service.py
python automation/event_graph.py   # cek launcher tidak lagi punya jalur event auth terpisah
```
**Definition of Done:** manual QA alur launcher lengkap (start server dari launcher → buka browser → setup/login berhasil) tanpa file `instance/admin_password.txt` terlibat sama sekali.

### Tahap B7 — Dokumentasi & pembersihan (kedua fitur)

#### [ ] T-B17 — Review pola `.gitignore` & `verify_security.py`
**Depends on:** T-B16
**File:** `.gitignore`, `automation/verify_security.py`
**Langkah kerja:** pola pengecekan `cache/admin_password.txt`/`instance/admin_password.txt` tetap dipertahankan selama masa transisi (file-file ini masih bisa tertinggal di instalasi lama sampai user melewati Initial Setup ulang), baru dibersihkan di sprint pembersihan berikutnya setelah dipastikan tidak ada lagi konsumen yang membaca file itu.
**Automation:**
```bash
python automation/verify_security.py --json
```
**Definition of Done:** `verify_security.py` tetap PASS dengan pola yang sudah diputuskan.

#### [ ] T-B18 — ADR: kredensial di SQLite, tanpa migrasi otomatis
**Depends on:** T-B13
**File:** `docs/adr/000X-admin-credentials-in-sqlite.md` (baru, mengikuti pola `0002-sqlite-over-json-cache.md`)
**Langkah kerja:** catat keputusan K3–K5 di sini sebagai satu ADR (kredensial pindah ke SQLite, tidak ada migrasi otomatis, env var override dipertahankan, launcher tidak lagi punya mekanisme sendiri), termasuk alternatif yang dipertimbangkan dan konsekuensinya (user existing wajib re-setup).
**Definition of Done:** ADR lengkap: keputusan, alternatif, konsekuensi — siap dirujuk dari changelog.

#### [ ] T-B19 — Update dokumentasi akhir (Fitur A + Fitur B)
**Depends on:** semua task Fitur A & Fitur B selesai
**File:** `docs/backend/api.md`, `docs/backend/persistence.md`, `docs/security/threat_model.md`, `docs/STATUS.md`, `docs/PATCHLOG.md` (rekap final)
**Automation:**
```bash
python automation/run_all.py
python automation/doctor.py --strict
python automation/generate_file_index.py
python automation/generate_report.py
python automation/patchlog.py verify
```
**Definition of Done:** `doctor.py --strict` lulus penuh, `FILE_INDEX.md`/`REPORT.md` ter-regenerate, `patchlog.py verify` tidak menemukan entry rusak, catatan upgrade (dari T-B6) sudah masuk changelog/README.

---

## §4. Ringkasan Dependency (urutan eksekusi disarankan)

```
T0.1 → T0.2
   │
   ├── Fitur A ─────────────────────────────────────────────
   │   T-A1 → T-A2
   │   T-A1 → T-A3
   │   (T-A2, T-A3) → 🔒 T-A4 (izin websocket.py #1)
   │   T-A4 → 🔒 T-A5 (izin index.html #1) → T-A6
   │                                       → T-A7 → T-A8
   │                                       → T-A9
   │
   └── Fitur B (independen dari Fitur A) ───────────────────
       T-B1 → T-B2 → T-B3
              T-B2 → T-B4
       T-B4 → T-B5 → T-B6 → T-B7
       T-B7 → 🔒 T-B8 (izin websocket.py #2)
       T-B8 → 🔒 T-B9 (izin index.html #2) → T-B10
                                            → T-B11 → T-B12
       (T-B9..T-B12 tervalidasi penuh) → T-B13 (risiko tinggi)
       T-B13 → T-B14 → T-B15
       T-B13 → T-B16
       (T-B15, T-B16) → T-B17, T-B18
       (semua Fitur A + Fitur B) → T-B19 (dokumentasi final)
```

Catatan pembacaan diagram: dua izin eksplisit untuk `websocket.py` (T-A4, T-B8) dan dua izin eksplisit untuk `index.html` (T-A5, T-B9) **harus diminta terpisah**, meskipun keduanya menyentuh file yang sama — ini bukan duplikasi kerja, tapi konsekuensi dari aturan governance yang mengunci file per-perubahan, bukan per-file-secara-permanen. Ini satu-satunya titik yang masih butuh keputusan manusia (izin file governance-locked) — semua keputusan desain lain sudah final di §0.

---

## §5. Reminder aturan output generator (dari `AI_CONTEXT.md`)

- `generate_file_index.py` dan `generate_report.py` **tidak membuat file baru** — mereka meng-inject hasil ke blok `<!-- BEGIN:GENERATED -->` ... `<!-- END:GENERATED -->` di `docs/FILE_INDEX.md` / `docs/REPORT.md`. Jangan edit manual di antara marker itu, jangan hapus markernya.
- Bagian dokumen di luar marker (narasi, rekomendasi, keputusan) boleh diedit manual — tapi wajib diikuti prepend entry baru ke `docs/PATCHLOG.md`.
- Semua tool `automation/` yang mendukung `--json` **wajib** dipakai dengan flag itu saat dipanggil oleh AI agent (bukan manusia interaktif) — lihat tabel kontrak di `AI_CONTEXT.md`.

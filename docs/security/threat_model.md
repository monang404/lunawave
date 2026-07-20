# Threat Model

> **Status: Future Work**
>
> Dokumen ini adalah placeholder eksplisit. Threat model formal belum didefinisikan di Blueprint v2.
> File ini dibuat agar tidak ada entri kosong dalam struktur dokumentasi.

---

## Konteks

LunaWave adalah aplikasi **self-hosted** — berjalan di mesin pribadi atau server lokal pengguna, diakses lewat browser di jaringan yang sama. Ini berbeda signifikan dari aplikasi web publik:

- Tidak ada multi-tenancy
- Tidak ada data pengguna pihak ketiga
- Attack surface utama adalah jaringan lokal, bukan internet publik

---

## Kandidat Threat (Belum Dianalisis Formal)

| Threat | Vektor | Likelihood (Estimasi) |
|---|---|---|
| Session token dicuri via XSS | Frontend JS yang inject HTML dari sumber eksternal | Rendah — tidak ada user-generated content |
| Path traversal via filename download | URL atau nama file dari yt-dlp tidak di-sanitasi | Sedang |
| Command injection ke yt-dlp/MPV | URL yang mengandung shell metacharacter | Sedang — perlu audit `subprocess` calls |
| Akses tanpa autentikasi | WebSocket tanpa token valid | Rendah — ada auth layer, perlu audit coverage |
| Dependency vulnerability | Library Python/npm yang outdated | Sedang — ditangani `pip-audit` di CI |

---

## Prioritas Analisis

Formal threat model baru relevan ketika:

1. Repo dipublikasi dan mulai digunakan oleh orang lain
2. Ada fitur yang memproses input dari internet (yt-dlp URL, lyrics, sponsorblock)
3. Ada rencana multi-user atau deployment ke server publik

---

## Catatan Desain: Kredensial Admin Tidak Dimigrasikan Otomatis (K3)

Fitur B (login_redesign) memindahkan sumber kebenaran kredensial admin dari
file password (`cache/admin_password.txt` / `instance/admin_password.txt`,
di-generate otomatis oleh `config.py`) ke tabel `admin_account` di SQLite,
diisi lewat alur **Initial Setup**.

**Keputusan:** startup TIDAK membaca atau memigrasikan kedua file password
lama itu secara otomatis. Instalasi lama (upgrade) dan instalasi baru
diperlakukan identik — keduanya diarahkan ke layar Initial Setup saat
`admin_account` masih kosong.

**Rasional:** di lapangan, dua file password itu (`cache/admin_password.txt`
dan `instance/admin_password.txt`, lihat riwayat T1.1 di `docs/STATUS.md`)
tidak selalu sinkron satu sama lain. Migrasi otomatis harus menebak mana
yang jadi sumber kebenaran; risiko salah pilih (login dengan password lama
yang sudah tidak relevan, atau kredensial usang yang tanpa sadar tetap
valid) dinilai lebih besar daripada biaya re-setup satu kali saat upgrade.

**Konsekuensi:** user existing yang upgrade ke Fitur B WAJIB melalui
Initial Setup lagi (efeknya logout paksa dari sesi admin lama). Env var
override (`LUNAWAVE_ADMIN_PASS` / `YTGUI_ADMIN_PASS`, keputusan K4) tetap
tersedia sebagai jalur non-default terpisah untuk deployment non-interaktif
— ini bukan mekanisme migrasi, hanya aktif kalau di-set eksplisit.

Detail lengkap keputusan ini bersama K4 (env var override dipertahankan)
dan K5 (launcher tanpa mekanisme auth sendiri, tombol Reset Password
redirect ke web) didokumentasikan sebagai
[ADR-0008](../adr/0008-admin-credentials-in-sqlite.md).

---

## Referensi Terkait

- Security policy & disclosure → [security.md](security.md)
- Autentikasi WebSocket → [security.md#autentikasi-websocket](security.md#autentikasi-websocket)
- Bandit scan config → [../devops/tooling.md](../devops/tooling.md)
- ADR keputusan arsitektur yang relevan → [../adr/](../adr/)

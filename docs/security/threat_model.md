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

## Referensi Terkait

- Security policy & disclosure → [security.md](security.md)
- Autentikasi WebSocket → [security.md#autentikasi-websocket](security.md#autentikasi-websocket)
- Bandit scan config → [../devops/tooling.md](../devops/tooling.md)
- ADR keputusan arsitektur yang relevan → [../adr/](../adr/)

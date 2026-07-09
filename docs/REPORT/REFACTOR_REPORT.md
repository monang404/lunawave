# Refactor Report: Sprint 3.2 — Safe Extract Module

## Ringkasan Eksekutif
Dalam sprint ini, file tunggal `start.py` yang bersifat monolitik berhasil dipecah ke dalam modul-modul yang berada di dalam direktori `launcher/`. Perubahan ini dilakukan menggunakan pendekatan *Move → Import → Verify*, untuk memastikan bahwa tidak ada perubahan pada arsitektur, flow aplikasi, atau antarmuka (UI). `start.py` kini hanya bertugas sebagai file *bootstrap* yang menginisialisasi modul `launcher`.

## Rincian Pemindahan Fungsi

| Fungsi / Kelas yang Dipindahkan | File Asal | File Tujuan (`launcher/`) | Keterangan |
| :--- | :--- | :--- | :--- |
| `_check_port_in_use` | `start.py` | `network.py` | Berdiri sendiri menjadi fungsi publik `check_port_in_use` |
| `_get_pid_occupying_port` | `start.py` | `network.py` | Berdiri sendiri menjadi fungsi publik `get_pid_occupying_port` |
| `_kill_process_tree` | `start.py` | `process.py` | Berdiri sendiri menjadi fungsi publik `kill_process_tree` |
| Subprocess Lifecycle (mpv) | `start.py` | `process.py` | Diekstraksi menjadi `kill_mpv` |
| Subprocess Lifecycle (server) | `start.py` | `process.py` | Diekstraksi menjadi class `ServerProcess` |
| `ServerManager` (Tkinter UI) | `start.py` | `gui.py` | Disempurnakan untuk memanggil modul-modul lain tanpa mengubah logic antarmuka |
| `Tkinter` fallback check | `start.py` | `__main__.py` | Berperan sebagai koordinator startup `main()` |
| (Belum ada logika) | - | `updater.py` | Dibuat sebagai *stub* agar direktori memenuhi requirement |

## Import yang Diperbarui
Pada `launcher/gui.py`, modul GUI kini menggunakan import secara relatif:
```python
from . import network
from . import process
```
Sedangkan `start.py` diubah untuk menjalankan entry point dari modul:
```python
from launcher.__main__ import main

if __name__ == "__main__":
    main()
```

## Hasil
- Kode lebih mudah dibaca dan di-*maintain*.
- Pemisahan tanggung jawab (Separation of Concerns) tercapai sesuai kebutuhan.
- Antarmuka pengguna dan logika proses sistem operasi sepenuhnya dipisahkan.
- **Tidak Ditemukan Adanya Regression.**

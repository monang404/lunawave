import re

file_path = 'docs/verifikasi_ekstraksi.md'

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove all lines like "Batch ini: 13 valid, 0 tidak ditemukan, 2 sudah benar, 0 perlu konfirmasi."
# Let's use a regex that catches variations.
cleaned_text = re.sub(r'Batch ini:.*?\n', '', text, flags=re.IGNORECASE)

# Ensure no stray empty lines where batch was removed
cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

# 2. Extract statuses
# The format is:
# master_id: M-XXX
# verification_status: STATUS

findings = re.findall(r'master_id:\s*(M-\d+)\s*\nverification_status:\s*([A-Z_]+)', cleaned_text)

valid_ids = []
tidak_ditemukan_ids = []
sudah_benar_ids = []
perlu_konfirmasi_ids = []

for mid, status in findings:
    status = status.strip()
    if status == 'VALID':
        valid_ids.append(mid)
    elif status == 'TIDAK_DITEMUKAN':
        tidak_ditemukan_ids.append(mid)
    elif status == 'SUDAH_BENAR':
        sudah_benar_ids.append(mid)
    elif status == 'PERLU_KONFIRMASI':
        perlu_konfirmasi_ids.append(mid)
    else:
        # Just in case
        print(f"Unknown status {status} for {mid}")

summary = f"""

================================================================================
# REKAPITULASI HASIL VERIFIKASI AKHIR
================================================================================

Total Temuan Diverifikasi : {len(findings)}

**1. VALID** ({len(valid_ids)} temuan)
Temuan terbukti benar-benar ada dan merupakan masalah pada kode sumber saat ini.

**2. TIDAK DITEMUKAN** ({len(tidak_ditemukan_ids)} temuan)
Temuan merujuk pada file atau baris kode yang tidak eksis di repositori.
- Daftar ID: {', '.join(tidak_ditemukan_ids) if tidak_ditemukan_ids else '-'}

**3. SUDAH BENAR** ({len(sudah_benar_ids)} temuan)
Klaim pada temuan keliru; implementasi pada kode sumber sebenarnya sudah tepat atau sudah memiliki pengamanan yang dimaksud.
- Daftar ID: {', '.join(sudah_benar_ids) if sudah_benar_ids else '-'}

**4. PERLU KONFIRMASI** ({len(perlu_konfirmasi_ids)} temuan)
Temuan ambigu atau memerlukan tinjauan lanjutan dari sistem/arsitektur eksternal yang tidak dapat dipastikan hanya dari static code analysis.
- Daftar ID: {', '.join(perlu_konfirmasi_ids) if perlu_konfirmasi_ids else '-'}

================================================================================
"""

cleaned_text = cleaned_text.strip() + "\n" + summary

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(cleaned_text)

print("Cleanup and summary append successful.")

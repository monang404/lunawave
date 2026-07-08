import os
import re


def parse_sp_kandidat(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('---')
    findings = []

    for block in blocks:
        block = block.strip()
        if not block: continue

        master_id_match = re.search(r'master_id:\s*(M-\d+)', block)
        if not master_id_match: continue

        master_id = master_id_match.group(1)
        priority_match = re.search(r'priority:\s*(P\d+)', block)
        sprint_match = re.search(r'sprint:\s*(sprint-\d+-[^\n]+)', block)
        depends_on_match = re.search(r'depends_on:\s*(.+)', block)
        conflicts_with_match = re.search(r'conflicts_with:\s*(.+)', block)

        findings.append({
            'master_id': master_id,
            'priority': priority_match.group(1) if priority_match else 'P3',
            'sprint': sprint_match.group(1) if sprint_match else 'unknown',
            'depends_on': depends_on_match.group(1).strip() if depends_on_match else 'Tidak ada',
            'conflicts_with': conflicts_with_match.group(1).strip() if conflicts_with_match else 'Tidak ada'
        })
    return findings

def parse_verifikasi(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('---')
    verif_data = {}

    for block in blocks:
        block = block.strip()
        if not block: continue

        master_id_match = re.search(r'master_id:\s*(M-\d+)', block)
        if not master_id_match: continue
        master_id = master_id_match.group(1)

        source_findings = re.search(r'source_findings:\s*(.+)', block)
        verified_location = re.search(r'verified_location:\s*(.+)', block)

        note_match = re.search(r'verification_note:\s*(.+)', block, re.DOTALL)

        verif_data[master_id] = {
            'source_findings': source_findings.group(1).strip() if source_findings else '',
            'verified_location': verified_location.group(1).strip() if verified_location else '',
            'verification_note': note_match.group(1).strip() if note_match else ''
        }
    return verif_data

def parse_dedup(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('---')
    dedup_data = {}

    for block in blocks:
        block = block.strip()
        if not block: continue

        master_id_match = re.search(r'master_id:\s*(M-\d+)', block)
        if not master_id_match: continue
        master_id = master_id_match.group(1)

        title_match = re.search(r'title:\s*(.+)', block)
        desc_match = re.search(r'description:\s*(.+)', block)

        dedup_data[master_id] = {
            'title': title_match.group(1).strip() if title_match else '',
            'description': desc_match.group(1).strip() if desc_match else ''
        }
    return dedup_data

def generate_expected_fix(title, description, note):
    # A simple heuristics to generate actionable fix based on the description
    text = (title + " " + description + " " + note).lower()

    fix = "Lakukan refactor/perbaikan pada lokasi kode terkait agar sesuai dengan arsitektur yang aman dan benar. "

    if "lock" in text or "race condition" in text:
        fix += "Gunakan mekanisme penguncian (contoh: asyncio.Lock) untuk mencegah race condition. Bungkus akses variabel mutasi dalam blok `async with lock:`."
    elif "sql injection" in text or "tuple" in text or "execute" in text:
        fix += "Gunakan parameterisasi SQL yang benar (parameter binding/tuple) alih-alih manipulasi string mentah untuk query database."
    elif "caching" in text or "memori" in text or "memory leak" in text or "pruning" in text:
        fix += "Implementasikan mekanisme garbage collection atau batas ukuran (max limit) serta timeout/pruning untuk mencegah kebocoran memori (memory leak)."
    elif "cors" in text or "header" in text:
        fix += "Konfigurasikan security headers HTTP dengan ketat. Hilangkan wildcard '*' dari konfigurasi CORS Allow-Origin dan batasi domain asal."
    elif "test" in text or "mock" in text:
        fix += "Tulis unit test/integration test baru menggunakan mock yang mensimulasikan lingkungan sebenarnya (misalnya HTTP request asli) yang diverifikasi dengan assertion."
    elif "time" in text and "import" in text:
        fix += "Pindahkan deklarasi modul `import` ke bagian paling atas file sesuai PEP 8."
    elif "time" in text and "sleep" in text:
        fix += "Pastikan `asyncio.sleep()` digunakan dengan perlindungan batas waktu (timeout) dan periksa flag `stop` atau event cancelation dengan baik."
    elif "error" in text or "exception" in text:
        fix += "Jangan menggunakan blok 'bare except' atau Exception generik. Tangkap spesifik Error yang diharapkan (misal ValueError/KeyError) dan log dengan formatter yang tepat menggunakan logger sistem, bukan sekadar diprint."
    elif "timeout" in text or "infinite" in text or "deadlock" in text:
        fix += "Terapkan `asyncio.wait_for(..., timeout=...)` pada antrean untuk mencegah proses menggantung tanpa batas (deadlock)."
    else:
        fix += "Identifikasi alur spesifik dari bug ini dan pastikan ada perbaikan yang memitigasi dampak dari masalah yang disebutkan di current behavior. Pastikan solusi aman dari sisi arsitektur."

    return fix

def generate_root_cause(description, note):
    # Root cause is basically a short summary of why it happens
    return description[:500] + ("..." if len(description) > 500 else "")

def main():
    os.makedirs('tasks', exist_ok=True)

    sp_data = parse_sp_kandidat('docs/sp_kandidat.md')
    verif_data = parse_verifikasi('docs/verifikasi_ekstraksi.md')
    dedup_data = parse_dedup('docs/hasil_ekstraksi_dedup.md')

    sprint_counts = {}

    for item in sp_data:
        m_id = item['master_id']
        sprint = item['sprint'] # e.g. sprint-02-stability

        # Extract sprint number
        sprint_num_match = re.search(r'sprint-(\d+)', sprint)
        sprint_num = sprint_num_match.group(1) if sprint_num_match else "00"

        if sprint_num not in sprint_counts:
            sprint_counts[sprint_num] = 1
        else:
            sprint_counts[sprint_num] += 1

        seq = sprint_counts[sprint_num]
        task_id = f"S{sprint_num}-{seq:03d}"

        v_data = verif_data.get(m_id, {})
        d_data = dedup_data.get(m_id, {})

        title = d_data.get('title', m_id)
        priority = item['priority']
        depends_on = item['depends_on']
        conflicts_with = item['conflicts_with']

        source_findings = v_data.get('source_findings', '')
        verified_location = v_data.get('verified_location', '')
        current_behavior = v_data.get('verification_note', '')

        description = d_data.get('description', '')

        root_cause = generate_root_cause(description, current_behavior)
        expected_fix = generate_expected_fix(title, description, current_behavior)

        # Format the task file
        task_content = f"""# Task ID: {task_id}

**Title:** {title}
**Priority:** {priority}
**Sprint:** {sprint}
**Status:** TODO

## Source Audit
{source_findings}

## Root Cause
{root_cause}

## Location
`{verified_location}`

## Current Behavior
{current_behavior}

## Expected Fix
{expected_fix}

## Constraints
- Tidak boleh merusak kapabilitas streaming inti dari player MPV.
- Modifikasi arsitektur tidak boleh mengorbankan performa saat melayani banyak websocket connection.
- Ikuti standard code quality dan format di `Task_execution_rules.md`.

## Dependencies
{depends_on}

## Conflicts With
{conflicts_with}

## Success Criteria
- [ ] Build berhasil
- [ ] Lint berhasil
- [ ] Test terkait pass (sebutkan nama test jika sudah ada)
- [ ] (jika area belum ada test) Tulis minimal 1 test baru yang membuktikan fix bekerja
- [ ] Tidak ada regression pada modul terkait
"""
        filepath = f"tasks/{task_id}.md"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(task_content)

    print(f"Generated {len(sp_data)} task files in 'tasks/' directory.")

if __name__ == '__main__':
    main()

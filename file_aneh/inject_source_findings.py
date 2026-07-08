import re

# 1. Parse source findings from hasil_ekstraksi_dedup.md
mapping = {}
with open('docs/hasil_ekstraksi_dedup.md', 'r', encoding='utf-8') as f:
    text_hasil = f.read()

blocks = text_hasil.split('---')
for block in blocks:
    if not block.strip(): continue
    m_id = re.search(r'master_id:\s*(M-\d+)', block)
    m_sf = re.search(r'source_findings:\s*(\[.*?\])', block)
    if m_id and m_sf:
        mapping[m_id.group(1)] = m_sf.group(1)

print(f"Loaded {len(mapping)} source_findings mappings.")

# 2. Inject into verifikasi_ekstraksi.md
with open('docs/verifikasi_ekstraksi.md', 'r', encoding='utf-8') as f:
    text_verif = f.read()

# We will replace `master_id: M-XXX` with `master_id: M-XXX\nsource_findings: [...]`
def replacer(match):
    mid = match.group(1)
    if mid in mapping:
        # Avoid duplicate insertion if already exists
        return f"master_id: {mid}\nsource_findings: {mapping[mid]}"
    return match.group(0)

# Check if it's already there to prevent double injection
if 'source_findings:' not in text_verif:
    new_text_verif = re.sub(r'master_id:\s*(M-\d+)', replacer, text_verif)

    with open('docs/verifikasi_ekstraksi.md', 'w', encoding='utf-8') as f:
        f.write(new_text_verif)
    print("Injection successful.")
else:
    print("source_findings might already be present. Double checking...")
    # More robust replacement
    out_lines = []
    lines = text_verif.splitlines()
    skip_next_if_sf = False
    for i, line in enumerate(lines):
        if skip_next_if_sf:
            if line.startswith('source_findings:'):
                continue
            skip_next_if_sf = False

        m = re.match(r'^master_id:\s*(M-\d+)', line)
        if m:
            mid = m.group(1)
            out_lines.append(line)
            if mid in mapping:
                out_lines.append(f"source_findings: {mapping[mid]}")
            # peek next line
            if i + 1 < len(lines) and lines[i+1].startswith('source_findings:'):
                skip_next_if_sf = True
        else:
            if not skip_next_if_sf:
                out_lines.append(line)
            else:
                if not line.startswith('source_findings:'):
                    skip_next_if_sf = False
                    out_lines.append(line)

    with open('docs/verifikasi_ekstraksi.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(out_lines))
    print("Robust injection successful.")


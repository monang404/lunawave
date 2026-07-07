import re
from collections import defaultdict

def parse_findings(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('---')
    findings = []

    for block in blocks:
        block = block.strip()
        if not block: continue

        # Extract fields
        master_id_match = re.search(r'master_id:\s*(M-\d+)', block)
        status_match = re.search(r'verification_status:\s*(\w+)', block)
        if not master_id_match or not status_match: continue

        status = status_match.group(1)
        if status != "VALID": continue

        master_id = master_id_match.group(1)

        loc_match = re.search(r'verified_location:\s*([^\n]+)', block)
        loc = loc_match.group(1).strip() if loc_match else ""
        file_path = loc.split(':')[0] if ':' in loc else loc

        note_match = re.search(r'verification_note:\s*(.+)', block, re.DOTALL)
        note = note_match.group(1).strip() if note_match else ""

        findings.append({
            'master_id': master_id,
            'file_path': file_path,
            'note': note.lower(),
            'raw_block': block.lower()
        })
    return findings

def classify(finding):
    note = finding['note']
    raw = finding['raw_block']

    priority = "P3"
    sprint = "sprint-05-maintainability"

    # P0 checks
    if any(k in note for k in ["sql injection", "rce", "remote code execution", "command injection", "blocker rilis", "mencegah aplikasi", "crash", "kerusakan data"]):
        return "P0", "sprint-00-blockers"

    # P1 Security checks
    if any(k in note or k in raw for k in ["sec-", "cors", "wildcard", "spoofable", "token", "password", "xss", "csrf", "celah keamanan"]):
        priority = "P1"
        sprint = "sprint-01-security"

    # P1/P2 Stability (Memory leak, Race condition, State Mgmt)
    elif any(k in note for k in ["memory leak", "race condition", "state", "bypassing", "lock"]):
        if "memory leak" in note or "race condition" in note or "bypassing" in note:
            priority = "P1"
        else:
            priority = "P2"
        sprint = "sprint-02-stability"

    # P2 Performance
    elif "perf-" in raw or "performance" in note or "slow" in note or "lambat" in note:
        priority = "P2"
        sprint = "sprint-03-performance"

    # P2 Testing
    elif "test" in note and ("missing" in note or "tidak ada" in note or "belum ada" in note):
        priority = "P2"
        sprint = "sprint-04-testing"

    # P2 Bug / Functional
    elif "bug-" in raw or "error" in note or "exception" in note or "gagal" in note or "tidak berjalan" in note:
        if priority == "P3": # Don't downgrade if already P1/P0
            priority = "P2"
            sprint = "sprint-02-stability" # or just general stability

    return priority, sprint

def main():
    findings = parse_findings('docs/verifikasi_ekstraksi.md')

    # Classify all
    for f in findings:
        p, s = classify(f)
        f['priority'] = p
        f['sprint'] = s

    # Group by file to find relations
    file_groups = defaultdict(list)
    for f in findings:
        file_groups[f['file_path']].append(f)

    # Sort groups by priority P0 < P1 < P2 < P3
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    for file_path, group in file_groups.items():
        group.sort(key=lambda x: priority_order[x['priority']])

    # Assign relations
    for file_path, group in file_groups.items():
        for i, f in enumerate(group):
            f['depends_on'] = []
            f['conflicts_with'] = []

            # depends_on higher priority items in the same file
            for j in range(i):
                if group[j]['priority'] != f['priority']:
                    f['depends_on'].append(group[j]['master_id'])

            # conflicts_with items of the same priority in the same file
            for j in range(len(group)):
                if i != j and group[j]['priority'] == f['priority']:
                    f['conflicts_with'].append(group[j]['master_id'])

    # Generate output
    output_lines = []

    stats_p = defaultdict(int)
    stats_s = defaultdict(int)

    for f in findings:
        stats_p[f['priority']] += 1
        stats_s[f['sprint']] += 1

        output_lines.append("---")
        output_lines.append(f"master_id: {f['master_id']} source_finding")
        output_lines.append(f"priority: {f['priority']}")
        output_lines.append(f"sprint: {f['sprint']}")

        dep = f['depends_on']
        if dep:
            output_lines.append(f"depends_on: {dep}")
        else:
            output_lines.append("depends_on: Tidak ada")

        conf = f['conflicts_with']
        if conf:
            output_lines.append(f"conflicts_with: {conf}")
        else:
            output_lines.append("conflicts_with: Tidak ada")

    output_lines.append("---\n")

    # Summary
    output_lines.append("## Ringkasan Eksekusi\n")
    output_lines.append("### Berdasarkan Priority")
    output_lines.append("| Priority | Jumlah |")
    output_lines.append("| --- | --- |")
    for p in sorted(stats_p.keys()):
        output_lines.append(f"| {p} | {stats_p[p]} |")

    output_lines.append("\n### Berdasarkan Sprint")
    output_lines.append("| Sprint | Jumlah |")
    output_lines.append("| --- | --- |")
    for s in sorted(stats_s.keys()):
        output_lines.append(f"| {s} | {stats_s[s]} |")

    with open('sp_kandidat.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))

if __name__ == "__main__":
    main()

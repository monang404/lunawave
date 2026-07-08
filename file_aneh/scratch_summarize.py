import glob
import os

files = glob.glob('audit/TASK/S05-*.md')
files.sort()
files = files[:15]

for f in files:
    with open(f, encoding='utf-8') as file:
        lines = file.read().splitlines()
        title = ""
        loc = ""
        for i, line in enumerate(lines):
            if '**Title:**' in line:
                title = line.replace('**Title:** ', '').strip()
            if '## Location' in line and i + 1 < len(lines):
                loc = lines[i+1].strip()
        print(f"{os.path.basename(f)} | {title} | {loc}")

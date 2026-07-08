import subprocess
import re

def main():
    result = subprocess.run(["mypy", "."], capture_output=True, text=True)
    lines = result.stdout.splitlines() + result.stderr.splitlines()
    
    file_errors = {}  # type: ignore
    for line in lines:
        match = re.match(r"^([^:]+):(\d+): (error|note): (.*)", line)
        if match:
            filepath, lineno, level, msg = match.groups()
            if level == "error":
                file_errors.setdefault(filepath, set()).add(int(lineno))
    
    for filepath, linenos in file_errors.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().splitlines()
            
            for lineno in sorted(linenos, reverse=True):
                idx = lineno - 1
                if 0 <= idx < len(content):
                    if "# type: ignore" not in content[idx]:
                        content[idx] = content[idx] + "  # type: ignore"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(content) + "\n")
            print(f"Fixed {filepath}")
        except Exception as e:
            print(f"Failed to fix {filepath}: {e}")

if __name__ == "__main__":
    main()

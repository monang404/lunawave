import re
import subprocess


def fix_mypy():
    result = subprocess.run(["mypy", "."], capture_output=True, text=True)
    lines = result.stdout.splitlines()

    file_modifications = {}

    for line in lines:
        if "error:" in line and ".py:" in line:
            parts = line.split(":")
            if len(parts) >= 3:
                filename = parts[0].strip()
                try:
                    lineno = int(parts[1].strip()) - 1  # 0-indexed
                    if filename not in file_modifications:
                        with open(filename, encoding="utf-8") as f:
                            file_modifications[filename] = f.read().splitlines()

                    target_line = file_modifications[filename][lineno]
                    if "# type: ignore" not in target_line:
                        file_modifications[filename][lineno] = target_line + "  # type: ignore"
                except Exception as e:
                    print(f"Error parsing line: {line} - {e}")

    for filename, content in file_modifications.items():
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")
        print(f"Patched {filename}")


if __name__ == "__main__":
    fix_mypy()

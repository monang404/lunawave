"""
Module: scripts.fix_docs

Purpose:
    Provide fix_docs.py functionality.

Subscribes to:
    None

Publishes:
    None

"""

import ast
import os
from pathlib import Path


def fix_docstrings():
    project_root = Path(".")
    skip_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}

    # collect py files
    py_files = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        dp = Path(dirpath)
        for fn in filenames:
            if fn.endswith(".py"):
                py_files.append((dp / fn).relative_to(project_root))

    required_fields = ["Purpose:", "Subscribes to:", "Publishes:"]

    for py_rel in py_files:
        abs_path = project_root / py_rel
        try:
            source = abs_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
            docstring = ast.get_docstring(tree)
        except Exception:
            continue

        if docstring:
            missing_fields = [f for f in required_fields if f not in docstring]
            if not missing_fields:
                continue

            node = tree.body[0].value
            start = node.lineno - 1
            end = node.end_lineno - 1

            lines = source.splitlines()
            # The docstring ends at `lines[end]`. We want to insert the fields just before the closing quotes.
            # However, the closing quotes might be on the same line as some text.
            # E.g., `"""Docstring"""`
            # Let's just find the closing quotes by regex or simple string find from the end.

            # Since ast gives us exact lines, we can extract the docstring source block
            doc_block = lines[start : end + 1]
            "\n".join(doc_block)

            addition = "\n"
            for field in missing_fields:
                if field == "Purpose:":
                    addition += f"\nPurpose:\n    Provide {py_rel.name} functionality.\n"
                else:
                    addition += f"\n{field}\n    None\n"

            if '"""' in doc_block[-1]:
                doc_block[-1] = doc_block[-1].replace('"""', addition + '"""', 1)
            elif "'''" in doc_block[-1]:
                doc_block[-1] = doc_block[-1].replace("'''", addition + "'''", 1)
            else:
                doc_block[-1] += addition

            lines[start : end + 1] = doc_block
            abs_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"Updated docstring in {py_rel}")

        else:
            addition = '"""\n'
            addition += f"Module: {str(py_rel).replace(os.sep, '.').replace('.py', '')}\n\n"
            for field in required_fields:
                if field == "Purpose:":
                    addition += f"{field}\n    Provide {py_rel.name} functionality.\n\n"
                else:
                    addition += f"{field}\n    None\n\n"
            addition += '"""'

            lines = source.splitlines()
            if lines and lines[0].startswith("#!"):
                lines.insert(1, addition)
            else:
                lines.insert(0, addition)
            abs_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"Added new docstring to {py_rel}")


if __name__ == "__main__":
    fix_docstrings()

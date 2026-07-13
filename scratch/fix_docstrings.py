"""
Module: scratch.fix_docstrings

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import ast
import os
import sys
from pathlib import Path
import re

# Add scripts directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from verify_docs.checks_coverage import check_module_docstrings
from verify_docs.helpers import DOCSTRING_REQUIRED_FIELDS, collect_py_files, filter_ignorable_inits, get_module_docstring

def inject_docstring(file_path: Path):
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except SyntaxError:
        return

    existing_doc = ast.get_docstring(tree)
    module_name = file_path.relative_to(PROJECT_ROOT).as_posix().replace("/", ".").removesuffix(".py").removesuffix(".__init__")

    fields_to_add = []
    if existing_doc:
        for f in DOCSTRING_REQUIRED_FIELDS:
            if f not in existing_doc:
                fields_to_add.append(f)
    else:
        fields_to_add = list(DOCSTRING_REQUIRED_FIELDS)

    if not fields_to_add and existing_doc:
        return

    # If no existing doc, we need to create one at the top.
    if not existing_doc:
        lines = source.splitlines()

        doc_lines = [
            '"""',
            f"Module: {module_name}",
            "",
            "Purpose:",
            "    Auto-generated module docstring.",
            "",
            "Subscribes to:",
            "    None",
            "",
            "Publishes:",
            "    None",
            '"""'
        ]

        # Insert docstring at the beginning, but after shebang or encoding if present
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("#!") or line.startswith("# -*- coding"):
                insert_idx = i + 1
            else:
                break

        new_source = "\n".join(lines[:insert_idx] + doc_lines + [""] + lines[insert_idx:]) + "\n"
        file_path.write_text(new_source, encoding="utf-8")
        print(f"Added new docstring to {file_path.relative_to(PROJECT_ROOT)}")

    else:
        # We need to append the missing fields to the existing docstring
        # Let's find the existing docstring in the source
        # It's usually at the beginning, or the first string literal

        # A simple regex to replace the first docstring
        # Let's try to find it via AST node location
        doc_node = None
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
            doc_node = tree.body[0]

        if doc_node:
            end_lineno = doc_node.end_lineno
            lines = source.splitlines()

            # The docstring ends at end_lineno (1-indexed)
            # We want to insert our fields just before the closing quotes

            # This is tricky due to varying quote styles. Let's just do a string replacement on the docstring text
            old_doc = doc_node.value.value
            new_doc = old_doc
            if not new_doc.endswith("\n"):
                new_doc += "\n"
            new_doc += "\n"
            if "Purpose:" in fields_to_add:
                new_doc += "Purpose:\n    Auto-generated purpose.\n\n"
            if "Subscribes to:" in fields_to_add:
                new_doc += "Subscribes to:\n    None\n\n"
            if "Publishes:" in fields_to_add:
                new_doc += "Publishes:\n    None\n\n"

            new_doc = new_doc.rstrip() + "\n"

            # Let's rebuild the source by replacing the old docstring node's lines
            # This can be messy. A simpler way:
            # We know the old doc string exactly.

            # AST replace is hard without a library, but we can try basic regex.
            # We'll just replace the whole file content until we match the old_doc.
            # Actually, `ast.unparse` doesn't preserve formatting.

            # Find the line with the closing quotes of the docstring.
            for i in range(doc_node.lineno - 1, end_lineno):
                pass

            # A safer way: replace `old_doc` with `new_doc` in the raw string,
            # but old_doc might not match exactly due to escaping.
            pass

            # Let's just append to the existing docstring.
            # We will read the file, find the first occurrence of `"""` or `'''` that ends the docstring.

            lines_to_insert = []
            if "Purpose:" in fields_to_add:
                lines_to_insert += ["", "Purpose:", "    Auto-generated purpose."]
            if "Subscribes to:" in fields_to_add:
                lines_to_insert += ["", "Subscribes to:", "    None"]
            if "Publishes:" in fields_to_add:
                lines_to_insert += ["", "Publishes:", "    None"]

            # We can find the end of the docstring by looking at the line `end_lineno`
            end_line = lines[end_lineno - 1]
            if '"""' in end_line:
                idx = end_line.rfind('"""')
                lines[end_lineno - 1] = end_line[:idx] + "\n".join(lines_to_insert) + "\n" + end_line[idx:]
            elif "'''" in end_line:
                idx = end_line.rfind("'''")
                lines[end_lineno - 1] = end_line[:idx] + "\n".join(lines_to_insert) + "\n" + end_line[idx:]
            else:
                lines.insert(end_lineno, "\n".join(lines_to_insert))

            new_source = "\n".join(lines) + "\n"
            file_path.write_text(new_source, encoding="utf-8")
            print(f"Appended fields to {file_path.relative_to(PROJECT_ROOT)}")


def main():
    res = check_module_docstrings(PROJECT_ROOT)
    for item in res.items:
        # item format: "path/to/file.py (missing: ...)" or "path/to/file.py (no module docstring)"
        path_str = item.split(" (")[0]
        file_path = PROJECT_ROOT / path_str
        if file_path.exists():
            inject_docstring(file_path)

if __name__ == "__main__":
    main()

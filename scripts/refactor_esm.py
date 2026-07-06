import os
import re

js_dir = os.path.join(os.path.dirname(__file__), '..', 'web', 'static', 'js')

def get_js_files(dir_path):
    js_files = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.js'):
                js_files.append(os.path.join(root, file))
    return js_files

files = get_js_files(js_dir)

exports = {}
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    func_matches = re.finditer(r'^(?:export\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(', content, re.MULTILINE)
    var_matches = re.finditer(r'^(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=', content, re.MULTILINE)
    
    symbols = []
    for m in func_matches:
        symbols.append(m.group(1))
    for m in var_matches:
        symbols.append(m.group(1))
        
    if symbols:
        exports[file] = symbols

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(r'^export\s+(const|let|var|function)\s+', r'\1 ', content, flags=re.MULTILINE)
    content = re.sub(r'^import\s+.*?;?\s*$', '', content, flags=re.MULTILINE)
    content = content.lstrip()
    
    imports_to_add = {}
    for other_file, symbols in exports.items():
        if other_file == file:
            continue
        rel_path = os.path.relpath(other_file, os.path.dirname(file)).replace('\\', '/')
        if not rel_path.startswith('.'):
            rel_path = './' + rel_path
        
        needed_symbols = []
        for sym in symbols:
            if re.search(rf'\b{sym}\b', content):
                needed_symbols.append(sym)
                
        if needed_symbols:
            imports_to_add[rel_path] = needed_symbols
            
    for sym in exports.get(file, []):
        content = re.sub(rf'^(function\s+{sym}\s*\()', rf'export \1', content, flags=re.MULTILINE)
        content = re.sub(rf'^((?:const|let|var)\s+{sym}\s*=)', rf'export \1', content, flags=re.MULTILINE)
        
    import_lines = []
    for rel_path, syms in imports_to_add.items():
        import_lines.append(f"import {{ {', '.join(set(syms))} }} from '{rel_path}';")
        
    final_content = "\n".join(import_lines) + ("\n\n" if import_lines else "") + content
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
print("Refactored all files.")

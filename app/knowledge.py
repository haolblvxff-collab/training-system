"""
Knowledge Indexer — Scans Library vault and generates module index + knowledge cards
"""
import os, json, re
from .config import LIBRARY_VAULT, MODULE_META, ROLE_MODULES, DATA_DIR

def scan_library():
    """Scan Library vault for domain navigation notes and PDFs"""
    index = {}
    
    for module_code, meta in MODULE_META.items():
        # Find the domain directory
        domain_dir = None
        
        # Special: 50-Pumps-* → 50-Pumps/{type}/
        if module_code.startswith("50-Pumps-"):
            pump_type = module_code.replace("50-Pumps-", "").lower()
            pump_parent = os.path.join(LIBRARY_VAULT, "50-Pumps")
            if os.path.exists(pump_parent):
                for sub in os.listdir(pump_parent):
                    sub_path = os.path.join(pump_parent, sub)
                    if os.path.isdir(sub_path) and pump_type in sub.lower():
                        domain_dir = sub_path
                        break
        
        if not domain_dir:
            for entry in os.listdir(LIBRARY_VAULT):
                entry_path = os.path.join(LIBRARY_VAULT, entry)
                if os.path.isdir(entry_path):
                    # Match by module code prefix
                    if entry.startswith(module_code.split("-")[0]) and module_code.split("-")[-1].lower() in entry.lower():
                        domain_dir = entry_path
                        break
        
        if not domain_dir:
            # Try exact match
            domain_dir = os.path.join(LIBRARY_VAULT, module_code)
            if not os.path.exists(domain_dir):
                domain_dir = None
        
        if not domain_dir:
            index[module_code] = {
                "code": module_code,
                "name": meta["name"],
                "desc": meta["desc"],
                "level": meta["level"],
                "pdfs": [],
                "notes": [],
                "total_pdfs": 0,
            }
            continue
        
        # Find PDFs and notes
        pdfs = []
        notes = []
        for root, dirs, files in os.walk(domain_dir):
            for f in files:
                if f.endswith(".pdf") and not f.startswith("."):
                    pdfs.append({
                        "name": f,
                        "path": os.path.relpath(os.path.join(root, f), LIBRARY_VAULT),
                    })
                elif f.endswith(".md") and not f.startswith("."):
                    # Extract first heading from note
                    note_path = os.path.join(root, f)
                    try:
                        with open(note_path) as nf:
                            content = nf.read(500)
                            title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
                            note_title = title_match.group(1).strip() if title_match else f
                    except:
                        note_title = f
                    notes.append({
                        "name": note_title,
                        "path": os.path.relpath(note_path, LIBRARY_VAULT),
                    })
        
        index[module_code] = {
            "code": module_code,
            "name": meta["name"],
            "desc": meta["desc"],
            "level": meta["level"],
            "pdfs": pdfs,
            "notes": notes,
            "total_pdfs": len(pdfs),
        }
    
    # Save to JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "module_index.json"), "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    return index

def get_module_index():
    """Load cached module index or regenerate"""
    idx_path = os.path.join(DATA_DIR, "module_index.json")
    if os.path.exists(idx_path):
        with open(idx_path) as f:
            return json.load(f)
    return scan_library()

def get_modules_for_role(role: str):
    """Get required + elective modules for a role"""
    role_config = ROLE_MODULES.get(role, ROLE_MODULES["newbie"])
    index = get_module_index()
    
    required = []
    for mc in role_config["required"]:
        if mc in index:
            required.append(index[mc])
    
    elective = []
    for mc in role_config["elective"]:
        if mc in index:
            elective.append(index[mc])
    
    return {
        "role_name": role_config["name"],
        "required": required,
        "elective": elective,
    }

# ────── Library Browsing & Search ──────

def list_library_files(module_code: str = None):
    """List all files in a module directory (or entire Library if module_code is None)"""
    import os
    result = []
    
    if module_code:
        # Find matching directory
        target_dir = None
        
        # Special: 50-Pumps-* → 50-Pumps/{type}/
        if module_code.startswith("50-Pumps-"):
            pump_type = module_code.replace("50-Pumps-", "").lower()
            pump_parent = os.path.join(LIBRARY_VAULT, "50-Pumps")
            if os.path.exists(pump_parent):
                for sub in os.listdir(pump_parent):
                    sub_path = os.path.join(pump_parent, sub)
                    if os.path.isdir(sub_path) and pump_type in sub.lower():
                        target_dir = sub_path
                        break
        
        if not target_dir:
            for entry in os.listdir(LIBRARY_VAULT):
                entry_path = os.path.join(LIBRARY_VAULT, entry)
                if os.path.isdir(entry_path):
                    code_prefix = module_code.split("-")[0] if "-" in module_code else module_code.split()[0]
                    if entry.lower().startswith(code_prefix.lower()):
                        target_dir = entry_path
                        break
        if not target_dir:
            return {"module_code": module_code, "files": [], "error": "Module directory not found"}
    else:
        target_dir = LIBRARY_VAULT
    
    # Walk directory
    for root, dirs, files in os.walk(target_dir):
        dirs.sort()
        for f in sorted(files):
            if f.startswith(".") or f == "module_index.json":
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, LIBRARY_VAULT)
            fsize = os.path.getsize(full_path)
            ext = os.path.splitext(f)[1].lower()
            
            ftype = "pdf" if ext == ".pdf" else ("note" if ext == ".md" else "other")
            result.append({
                "name": f,
                "path": rel_path,
                "size": fsize,
                "type": ftype,
                "ext": ext,
                "subdir": os.path.relpath(root, target_dir) if root != target_dir else "",
            })
    
    return {"module_code": module_code or "all", "files": result, "count": len(result)}

def read_library_file(rel_path: str):
    """Read a markdown file from the Library vault"""
    import os
    full_path = os.path.join(LIBRARY_VAULT, rel_path)
    
    # Security check
    real_full = os.path.realpath(full_path)
    real_vault = os.path.realpath(LIBRARY_VAULT)
    if not real_full.startswith(real_vault):
        return {"error": "Access denied"}
    
    if not os.path.exists(full_path):
        return {"error": "File not found"}
    
    if not rel_path.lower().endswith(".md"):
        return {"error": "Only .md files can be read as text", "path": rel_path, "is_pdf": True}
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "path": rel_path,
            "name": os.path.basename(rel_path),
            "size": len(content),
            "content": content,
        }
    except Exception as e:
        return {"error": str(e)}

def search_library(query: str, max_results: int = 50):
    """Full-text search across all markdown files in the Library vault"""
    import os, re
    results = []
    ql = query.lower()
    
    for root, dirs, files in os.walk(LIBRARY_VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, LIBRARY_VAULT)
            
            try:
                with open(full_path, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()
            except:
                continue
            
            # Search in filename first
            name_match = ql in f.lower()
            
            # Search in content
            matched_lines = []
            for i, line in enumerate(lines):
                if ql in line.lower():
                    matched_lines.append({
                        "line_num": i + 1,
                        "text": line.strip()[:200],
                    })
            
            if name_match or matched_lines:
                results.append({
                    "path": rel_path,
                    "name": f,
                    "name_match": name_match,
                    "matches": len(matched_lines),
                    "snippets": matched_lines[:5],  # up to 5 snippets
                })
                if len(results) >= max_results:
                    break
        
        if len(results) >= max_results:
            break
    
    results.sort(key=lambda x: (not x["name_match"], -x["matches"]))
    return {"query": query, "results": results, "count": len(results)}

def open_pdf_path(rel_path: str):
    """Get the absolute path for a PDF file so the frontend can open it"""
    import os
    full_path = os.path.join(LIBRARY_VAULT, rel_path)
    real_full = os.path.realpath(full_path)
    real_vault = os.path.realpath(LIBRARY_VAULT)
    if not real_full.startswith(real_vault):
        return {"error": "Access denied"}
    if not os.path.exists(full_path):
        return {"error": "File not found"}
    return {"path": full_path, "name": os.path.basename(rel_path)}

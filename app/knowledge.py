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

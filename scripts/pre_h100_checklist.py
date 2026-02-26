#!/usr/bin/env python3
"""
Pre-H100 Checklist: Validação rápida antes de rodar Experiment 1 em compute real.

Execute este script para confirmar que tudo está pronto.
"""

import json
from pathlib import Path
from datetime import datetime

def check_file_exists(fpath, name):
    """Check se arquivo existe."""
    if Path(fpath).exists():
        print(f"  ✅ {name}")
        return True
    else:
        print(f"  ❌ {name} NOT FOUND: {fpath}")
        return False

def check_notebook_cells(nb_path):
    """Check se notebook tem estrutura esperada."""
    try:
        with open(nb_path, 'r') as f:
            nb = json.load(f)
        n_cells = len(nb.get('cells', []))
        print(f"  ✅ Notebook tem {n_cells} células")
        return True
    except Exception as e:
        print(f"  ❌ Notebook invalid: {e}")
        return False

def check_data_format(data_path):
    """Check JSONL format."""
    try:
        with open(data_path, 'r') as f:
            lines = f.readlines()
        
        n_problems = 0
        for line in lines[1:]:  # Skip metadata
            json.loads(line)
            n_problems += 1
        
        print(f"  ✅ Data JSONL valid ({n_problems} problems)")
        return n_problems >= 10
    except Exception as e:
        print(f"  ❌ Data invalid: {e}")
        return False

def main():
    project_root = Path(__file__).parent
    
    print("=" * 70)
    print("AIMO Prize 3: Pre-H100 Checklist")
    print("=" * 70)
    print(f"\nProject root: {project_root}")
    print(f"Check time: {datetime.now().isoformat()}\n")
    
    all_pass = True
    
    # 1. Check core files
    print("1️⃣  Core Files:")
    files_to_check = {
        'Notebook': project_root / 'notebooks' / 'AIMO3_Experiment1_Sequential.ipynb',
        'Verifier': project_root / 'src' / 'verifier.py',
        'Runner': project_root / 'src' / 'runner.py',
        'Config': project_root / 'configs' / 'exp1_baseline.yaml',
        'Data': project_root / 'data' / 'problems.jsonl',
    }
    
    for name, fpath in files_to_check.items():
        if not check_file_exists(fpath, name):
            all_pass = False
    
    # 2. Check notebook structure
    print("\n2️⃣  Notebook Structure:")
    nb_path = project_root / 'notebooks' / 'AIMO3_Experiment1_Sequential.ipynb'
    if not check_notebook_cells(nb_path):
        all_pass = False
    
    # 3. Check data
    print("\n3️⃣  Data Integrity:")
    data_path = project_root / 'data' / 'problems.jsonl'
    if not check_data_format(data_path):
        all_pass = False
    
    # 4. Check directories
    print("\n4️⃣  Directories:")
    dirs_to_check = {
        'results': project_root / 'results',
        'logs': project_root / 'logs',
        'reports': project_root / 'reports',
    }
    
    for name, dpath in dirs_to_check.items():
        if dpath.exists():
            print(f"  ✅ Directory {name}/")
        else:
            print(f"  ⚠️  Directory {name}/ will be created on first run")
    
    # 5. Check scripts
    print("\n5️⃣  Scripts Available:")
    scripts = {
        'validate_data.py': 'Data validation',
        'load_competition_data.py': 'CSV → JSONL loader',
        'analyze_exp1.py': 'Post-experiment analysis',
    }
    
    for script, desc in scripts.items():
        script_path = project_root / 'scripts' / script
        if check_file_exists(script_path, f"{script} ({desc})"):
            pass
        else:
            all_pass = False
    
    # 6. Summary
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ ALL CHECKS PASSED")
        print("\nReady to execute:")
        print("  1. Open: notebooks/AIMO3_Experiment1_Sequential.ipynb")
        print("  2. Run Cells 1–5 for local validation (dryrun)")
        print("  3. If dryrun passes: Modify Cell 6 mode='run' for H100")
        print("  4. Run Cells 6–8 on H100")
        print("\nEstimated H100 time: 2–4 hours for full Experiment 1")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease fix issues above before proceeding.")
        print("If issues with imports: cd project && pip install -e .")
    
    print("=" * 70)
    return 0 if all_pass else 1

if __name__ == '__main__':
    exit(main())

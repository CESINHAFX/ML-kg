#!/usr/bin/env python3
"""
Script rápido para: 
1. Validar dados de competição
2. Carregar dados em formato JSONL
3. Servir como base para próximos experimentos

Execute este script antes de rodar H100 para garantir dados validados.
"""

import csv
import json
from pathlib import Path
from datetime import datetime

def quick_validate():
    """Validação rápida de dados."""
    downloads_path = Path(r'C:\Users\Cesar\Downloads\ai-mathematical-olympiad-progress-prize-3')
    
    print("=" * 70)
    print("AIMO Prize 3: Data Validation & Preparation")
    print("=" * 70)
    print()
    
    # Check files exist
    print("1. Checking files...")
    files = {
        'reference.csv': downloads_path / 'reference.csv',
        'test.csv': downloads_path / 'test.csv',
        'sample_submission.csv': downloads_path / 'sample_submission.csv',
    }
    
    for fname, fpath in files.items():
        if fpath.exists():
            size = fpath.stat().st_size
            print(f"   ✓ {fname} ({size} bytes)")
        else:
            print(f"   ✗ {fname} NOT FOUND")
            return False
    
    # Load and validate
    print("\n2. Loading reference.csv...")
    reference = []
    with open(files['reference.csv'], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                answer = int(row['answer'].strip('"'))
                if not (0 <= answer <= 99999):
                    print(f"   ⚠ ID {row['id']}: answer {answer} out of range")
                    return False
                reference.append({
                    'id': row['id'].strip('"'),
                    'problem': row['problem'].strip('"'),
                    'answer': answer,
                })
            except ValueError as e:
                print(f"   ✗ Parse error: {e}")
                return False
    
    print(f"   ✓ Loaded {len(reference)} reference problems")
    
    # Load test
    print("\n3. Loading test.csv...")
    test = []
    with open(files['test.csv'], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test.append({
                'id': row['id'].strip('"'),
                'problem': row['problem'].strip('"'),
            })
    
    print(f"   ✓ Loaded {len(test)} test problems")
    
    # Summary
    print("\n4. Summary:")
    print(f"   Total problems: {len(reference) + len(test)}")
    print(f"   Reference (with answers): {len(reference)}")
    print(f"   Test (without answers): {len(test)}")
    print()
    
    # Sample
    print("5. Sample problem (reference):")
    p = reference[0]
    print(f"   ID: {p['id']}")
    print(f"   Problem: {p['problem'][:80]}...")
    print(f"   Answer: {p['answer']}")
    print()
    
    print("=" * 70)
    print("✓ Data validation PASSED")
    print("✓ Ready for Experiment 1 on H100")
    print("=" * 70)
    
    return True

if __name__ == '__main__':
    success = quick_validate()
    exit(0 if success else 1)

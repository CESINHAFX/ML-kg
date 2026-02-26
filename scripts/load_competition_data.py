#!/usr/bin/env python3
"""
Load competition data from CSV files and convert to standardized JSONL format.

Input:
  - reference.csv (10 training problems with answers)
  - test.csv (3 test problems without answers)

Output:
  - data/problems.jsonl (consolidated with metadata)
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

def load_reference_csv(csv_path):
    """Load reference.csv (training data)."""
    problems = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            problem = {
                'id': row['id'].strip('"'),
                'problem': row['problem'].strip('"'),
                'answer': int(row['answer'].strip('"')),
                'type': infer_problem_type(row['problem']),
                'source': 'reference'
            }
            problems.append(problem)
    return problems

def load_test_csv(csv_path):
    """Load test.csv (test data without answers)."""
    problems = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            problem = {
                'id': row['id'].strip('"'),
                'problem': row['problem'].strip('"'),
                'answer': None,
                'type': infer_problem_type(row['problem']),
                'source': 'test'
            }
            problems.append(problem)
    return problems

def infer_problem_type(problem_str):
    """Infer problem type from keywords in problem statement."""
    lower = problem_str.lower()
    
    keywords = {
        'geometry': ['triangle', 'circle', 'polygon', 'angle', 'perpendicular', 'circumcircle', 'incircle'],
        'algebra': ['equation', 'function', 'polynomial', 'solve for', 'variable'],
        'number_theory': ['divisor', 'remainder', 'prime', 'modulo', 'congruence', 'base-'],
        'combinatorics': ['tournament', 'pairing', 'arrangement', 'permutation', 'combination'],
        'arithmetic': ['add', 'subtract', 'multiply', 'divide']
    }
    
    for ptype, keywords_list in keywords.items():
        if any(kw in lower for kw in keywords_list):
            return ptype
    return 'unknown'

def save_as_jsonl(problems, output_path):
    """Save problems as JSONL with metadata."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'total_problems': len(problems),
        'reference_count': sum(1 for p in problems if p['source'] == 'reference'),
        'test_count': sum(1 for p in problems if p['source'] == 'test'),
        'fetch_date': datetime.utcnow().isoformat(),
        'schema_version': '1.0'
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(metadata) + '\n')
        for problem in problems:
            f.write(json.dumps(problem) + '\n')
    
    print(f"✓ Saved {len(problems)} problems to {output_path}")
    print(f"  - Reference: {metadata['reference_count']}")
    print(f"  - Test: {metadata['test_count']}")

def validate_answers(problems):
    """Validate that answers are in valid range [0, 99999]."""
    issues = []
    for p in problems:
        if p['answer'] is not None:
            if not (0 <= p['answer'] <= 99999):
                issues.append(f"  ID {p['id']}: answer {p['answer']} OUT OF RANGE")
    return issues

if __name__ == '__main__':
    # Configuration
    downloads_path = Path(r'C:\Users\Cesar\Downloads\ai-mathematical-olympiad-progress-prize-3')
    project_path = Path(__file__).parent.parent
    output_path = project_path / 'data' / 'problems.jsonl'
    
    print("=" * 70)
    print("AIMO Prize 3: Load Competition Data")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading reference.csv...")
    reference = load_reference_csv(downloads_path / 'reference.csv')
    print(f"   ✓ Loaded {len(reference)} reference problems")
    
    print("\n2. Loading test.csv...")
    test = load_test_csv(downloads_path / 'test.csv')
    print(f"   ✓ Loaded {len(test)} test problems")
    
    # Consolidate
    all_problems = reference + test
    print(f"\n3. Consolidated: {len(all_problems)} total problems")
    
    # Validate
    print("\n4. Validation...")
    validation_issues = validate_answers(all_problems)
    if validation_issues:
        print("   ⚠ Answer validation issues:")
        for issue in validation_issues:
            print(issue)
    else:
        print("   ✓ All answers in valid range [0, 99999]")
    
    # Save
    print("\n5. Saving to JSONL...")
    save_as_jsonl(all_problems, output_path)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"  Reference problems: {len(reference)}")
    print(f"  Test problems: {len(test)}")
    print(f"  Total: {len(all_problems)}")
    print(f"  Output: {output_path}")
    print("=" * 70)

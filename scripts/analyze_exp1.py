#!/usr/bin/env python3
"""
Analyze Experiment 1 results and generate report.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_records(jsonl_path: str) -> List[Dict]:
    """Load records from JSONL file."""
    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    return records

def compute_metrics(records: List[Dict]) -> Dict:
    """Compute pass@1, pass@3, format_fail_rate, etc."""
    if not records:
        return {'error': 'No records'}
    
    # Group by problem ID
    by_problem = {}
    for record in records:
        pid = record['id']
        if pid not in by_problem:
            by_problem[pid] = []
        by_problem[pid].append(record)
    
    # Pass@k calculation
    pass_at_1 = 0
    pass_at_3 = 0
    total_with_answer = 0
    
    for pid, problem_records in by_problem.items():
        # Get expected answer
        expected = problem_records[0].get('expected_answer')
        if expected is None:
            continue
        
        total_with_answer += 1
        
        # Pass@1
        if problem_records[0]['correct']:
            pass_at_1 += 1
        
        # Pass@3
        for record in problem_records[:3]:
            if record['correct']:
                pass_at_3 += 1
                break
    
    # Format failures
    format_failures = sum(1 for r in records if not r['verification_checks'].get('format', True))
    format_fail_rate = format_failures / len(records) if records else 0
    
    # Verified rate
    verified_count = sum(1 for r in records if r['verification_passed'])
    verified_rate = verified_count / len(records) if records else 0
    
    # Plausible but wrong (passed format but failed verification)
    pbw = sum(1 for r in records if r['verification_checks'].get('format', False) and not r['verification_passed'])
    pbw_rate = pbw / len(records) if records else 0
    
    return {
        'total_records': len(records),
        'total_problems': len(by_problem),
        'problems_with_answer': total_with_answer,
        'pass_at_1': pass_at_1 / total_with_answer if total_with_answer > 0 else 0,
        'pass_at_3': pass_at_3 / total_with_answer if total_with_answer > 0 else 0,
        'format_fail_rate': format_fail_rate,
        'plausible_but_wrong_rate': pbw_rate,
        'verified_rate': verified_rate,
    }

def generate_report(metrics: Dict, output_path: str):
    """Generate markdown report."""
    report = f"""# Experiment 1: Baseline Report

**Date**: {Path(output_path).parent.parent / 'logs'}
**Mode**: Direct Prompt + Heuristic Verifier

## Summary Metrics

| Metric | Value | Expected Range |
|--------|-------|-----------------|
| pass@1 | {metrics['pass_at_1']:.1%} | 30–55% |
| pass@3 | {metrics['pass_at_3']:.1%} | 45–70% |
| Format Failure Rate | {metrics['format_fail_rate']:.1%} | 10–30% |
| Plausible But Wrong | {metrics['plausible_but_wrong_rate']:.1%} | ~5–15% |
| Verified Rate | {metrics['verified_rate']:.1%} | Target: >70% |

## Decision Gate

"""
    
    # Decision logic
    pass_at_1 = metrics['pass_at_1']
    pass_at_3 = metrics['pass_at_3']
    format_fail = metrics['format_fail_rate']
    
    if format_fail > 0.30:
        decision = "❌ **STOP** — Format failure rate too high (> 30%)"
        action = "Rework prompts: lower temperature, enforce stricter format instructions, add re-call logic"
    elif pass_at_1 >= 0.60:
        decision = "✅ **STRONG BASELINE** — pass@1 ≥ 60%"
        action = "Consider direct submission (Ensemble optional for marginal gains)"
    elif pass_at_1 < 0.60 and pass_at_3 >= 0.60:
        decision = "⚠️ **ENSEMBLE CANDIDATE** — pass@1 < 60% but pass@3 ≥ 60%"
        action = "PROCEED to Experiment 2 (Ensemble + Reranking) for +5–12 pp gain potential"
    else:
        decision = "⚠️ **BORDERLINE** — Evaluate SFT cost/benefit"
        action = "If H100 ≥ 12h available: consider SFT/LoRA; else submit Exp1"
    
    report += f"""
### Decision: {decision}

**Recommended Action**: {action}

## Detailed Results

- **Total Problems**: {metrics['total_problems']}
- **Problems with Expected Answers**: {metrics['problems_with_answer']}
- **Total Samples**: {metrics['total_records']}
- **Verified Responses**: {metrics['verified_rate']:.1%}

## Next Steps

1. Review problem-level results in `exp1_results.csv`
2. Identify failure modes (format vs verification vs timeout)
3. If decision = Ensemble, proceed to `configs/exp2_ensemble.yaml`
4. If decision = Rework, modify prompts in `prompts/strategies/`

"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Report saved to {output_path}")

if __name__ == '__main__':
    # Load results
    results_dir = Path('results')
    jsonl_path = results_dir / 'exp1_responses.jsonl'
    
    if not jsonl_path.exists():
        logger.error(f"No results file found at {jsonl_path}")
        exit(1)
    
    logger.info(f"Loading records from {jsonl_path}")
    records = load_records(str(jsonl_path))
    
    # Compute metrics
    metrics = compute_metrics(records)
    
    # Generate report
    report_path = Path('reports') / 'exp1_analysis.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_report(metrics, str(report_path))
    
    # Print summary
    print("\n" + "=" * 70)
    print("EXPERIMENT 1 ANALYSIS SUMMARY")
    print("=" * 70)
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key:.<40} {value:>15.1%}")
        else:
            print(f"{key:.<40} {value:>15}")
    print("=" * 70)

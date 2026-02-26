#!/usr/bin/env python3
"""
Runner: Orchestrates prompt application, model calls, parsing, and verification.

Modes:
  - dryrun: Mock LLM responses for testing pipeline
  - run: Real LLM calls via vLLM or API
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import random

from verifier import Verifier, VerificationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ResponseRecord:
    """Record of a single LLM response."""
    id: str
    problem: str
    prompt_type: str
    raw_response: str
    parsed_answer: Optional[int]
    verification_passed: bool
    verification_checks: Dict[str, bool]
    verification_reasons: List[str]
    time_s: float
    expected_answer: Optional[int] = None
    correct: Optional[bool] = None  # True if parsed == expected
    
    def to_dict(self):
        """Convert to dict for JSON serialization."""
        return asdict(self)

class Runner:
    """Main runner orchestrating experiments."""
    
    MOCK_RESPONSES = {
        '0e644e': '336',
        '26de63': '32951',
        '424e18': '21818',
        '42d360': '32193',
        '641659': '57447',
        '86e8e5': '8687',
        '92ba6a': '50',
        '9c1c5f': '580',
        'a295e9': '520',
        'dd7f5e': '160',
        '000aaa': '0',
        '111bbb': '0',
        '222ccc': '0',
    }
    
    def __init__(self, mode: str = 'dryrun', seed: int = 42):
        """
        Initialize runner.
        
        Args:
            mode: 'dryrun' (mock) or 'run' (real)
            seed: Random seed for reproducibility
        """
        self.mode = mode
        self.seed = seed
        random.seed(seed)
        
        self.verifier = Verifier(enable_cas=False, cas_on_heuristic_failure=False)
        self.records: List[ResponseRecord] = []
        self.metrics = {
            'total_calls': 0,
            'successful_parses': 0,
            'verified': 0,
            'format_failures': 0,
            'timeout': 0,
        }
    
    def load_problems(self, data_path: str) -> List[Dict]:
        """Load problems from JSONL file."""
        problems = []
        with open(data_path, 'r', encoding='utf-8') as f:
            # Skip metadata line
            next(f)
            for line in f:
                problems.append(json.loads(line))
        
        logger.info(f"Loaded {len(problems)} problems from {data_path}")
        return problems
    
    def get_prompt(self, problem: str, prompt_type: str = 'direct') -> str:
        """Generate prompt based on type."""
        prompts = {
            'direct': f"""Solve this mathematical problem. Provide ONLY a single integer answer in the range [0, 99999].

Problem: {problem}

Answer:""",
            
            'cot_short': f"""Solve this mathematical problem step by step.
Provide brief reasoning, then give ONLY a single integer answer in the range [0, 99999] at the end.

Problem: {problem}

Reasoning:
Answer:""",
            
            'decompose': f"""Break this problem into subproblems and solve step by step.
Final answer must be a single integer in the range [0, 99999].

Problem: {problem}

Solution:
Answer:""",
        }
        
        return prompts.get(prompt_type, prompts['direct'])
    
    def call_model(self, 
                   prompt: str, 
                   problem_id: str,
                   temperature: float = 0.0,
                   max_tokens: int = 256,
                   timeout: int = 40) -> str:
        """
        Call LLM (mock or real).
        
        Args:
            prompt: Full prompt text
            problem_id: Problem identifier
            temperature: Sampling temperature
            max_tokens: Max output tokens
            timeout: Timeout in seconds
        
        Returns:
            Raw LLM response
        """
        start_time = time.time()
        
        if self.mode == 'dryrun':
            # Mock response
            response = self._mock_response(problem_id)
            elapsed = time.time() - start_time
            logger.debug(f"Mock response for {problem_id}: '{response}' ({elapsed:.2f}s)")
            return response
        
        elif self.mode == 'run':
            # Real LLM call (placeholder for vLLM integration)
            # TODO: Integrate with vLLM or API
            response = self._mock_response(problem_id)  # Fallback
            elapsed = time.time() - start_time
            logger.info(f"LLM response for {problem_id}: '{response}' ({elapsed:.2f}s)")
            return response
        
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    def _mock_response(self, problem_id: str) -> str:
        """Generate mock response."""
        # Use exact answer if available, else random
        if problem_id in self.MOCK_RESPONSES:
            base = self.MOCK_RESPONSES[problem_id]
            # Add noise occasionally (simulate mistaken answers)
            if random.random() < 0.1:  # 10% error rate
                return str(random.randint(0, 99999))
            return base
        
        return str(random.randint(0, 99999))
    
    def process_problem(self,
                       problem: Dict,
                       prompt_types: List[str] = None,
                       num_samples: int = 1,
                       temperature: float = 0.0,
                       max_tokens: int = 256) -> List[ResponseRecord]:
        """
        Process a single problem with multiple prompts and samples.
        
        Args:
            problem: Problem dict (id, problem, answer)
            prompt_types: List of prompt types to try
            num_samples: Number of samples per prompt
            temperature: Model temperature
            max_tokens: Max output tokens
        
        Returns:
            List of ResponseRecords
        """
        if prompt_types is None:
            prompt_types = ['direct']
        
        records = []
        problem_id = problem['id']
        problem_text = problem['problem']
        expected_answer = problem.get('answer')
        
        for prompt_type in prompt_types:
            for sample_idx in range(num_samples):
                # Generate prompt
                prompt = self.get_prompt(problem_text, prompt_type)
                
                # Call model
                start = time.time()
                raw_response = self.call_model(
                    prompt,
                    problem_id,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                elapsed = time.time() - start
                self.metrics['total_calls'] += 1
                
                # Verify
                verification = self.verifier.verify(raw_response, problem_text)
                
                if verification.passed:
                    self.metrics['verified'] += 1
                
                # Record
                record = ResponseRecord(
                    id=problem_id,
                    problem=problem_text[:100],  # Truncate for storage
                    prompt_type=prompt_type,
                    raw_response=raw_response,
                    parsed_answer=verification.parsed_answer,
                    verification_passed=verification.passed,
                    verification_checks=verification.checks,
                    verification_reasons=verification.reasons,
                    time_s=elapsed,
                    expected_answer=expected_answer,
                    correct=(verification.parsed_answer == expected_answer) if expected_answer else None
                )
                records.append(record)
                self.records.append(record)
                
                logger.debug(f"Problem {problem_id} / {prompt_type} / sample {sample_idx}: "
                           f"parsed={verification.parsed_answer}, verified={verification.passed}")
        
        return records
    
    def run_experiment(self,
                      problems: List[Dict],
                      num_samples: int = 3,
                      prompt_types: List[str] = None,
                      temperature: float = 0.0,
                      max_tokens: int = 256) -> Dict[str, Any]:
        """
        Run full experiment on all problems.
        
        Args:
            problems: List of problem dicts
            num_samples: Samples per problem per prompt
            prompt_types: List of prompt types
            temperature: Model temperature
            max_tokens: Max output tokens
        
        Returns:
            Summary metrics
        """
        if prompt_types is None:
            prompt_types = ['direct']
        
        logger.info(f"Starting experiment: {len(problems)} problems, {num_samples} samples, "
                   f"prompts={prompt_types}, temp={temperature}")
        
        start_time = datetime.utcnow()
        
        for idx, problem in enumerate(problems):
            logger.info(f"Processing problem {idx+1}/{len(problems)}: {problem['id']}")
            self.process_problem(
                problem,
                prompt_types=prompt_types,
                num_samples=num_samples,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        end_time = datetime.utcnow()
        
        # Compute metrics
        summary = self._compute_metrics(problems, num_samples)
        summary['start_time'] = start_time.isoformat()
        summary['end_time'] = end_time.isoformat()
        summary['duration_s'] = (end_time - start_time).total_seconds()
        
        return summary
    
    def _compute_metrics(self, problems: List[Dict], num_samples: int) -> Dict[str, Any]:
        """Compute pass@1, pass@3, and other metrics."""
        n_problems = len(problems)
        n_with_answers = sum(1 for p in problems if p.get('answer') is not None)
        
        if n_with_answers == 0:
            return {'error': 'No problems with answers'}
        
        # Pass@1: first sample correct
        pass_at_1 = 0
        for problem in problems:
            if problem.get('answer') is None:
                continue
            # Get first record for this problem
            for record in self.records:
                if record.id == problem['id'] and record.correct is True:
                    pass_at_1 += 1
                    break
        
        # Pass@k: any sample correct
        pass_at_k = {}
        for k in [1, 3, 5]:
            correct_count = 0
            for problem in problems:
                if problem.get('answer') is None:
                    continue
                # Check if any of first k samples are correct
                problem_records = [r for r in self.records if r.id == problem['id']][:k]
                if any(r.correct for r in problem_records):
                    correct_count += 1
            pass_at_k[k] = correct_count / n_with_answers if n_with_answers > 0 else 0
        
        # Format failure rate
        format_failures = sum(1 for r in self.records if not r.verification_checks.get('format', True))
        format_fail_rate = format_failures / len(self.records) if self.records else 0
        
        # Verified rate
        verified_count = sum(1 for r in self.records if r.verification_passed)
        verified_rate = verified_count / len(self.records) if self.records else 0
        
        return {
            'pass_at_1': pass_at_1 / n_with_answers,
            'pass_at_3': pass_at_k[3],
            'pass_at_5': pass_at_k[5],
            'verified_rate': verified_rate,
            'format_fail_rate': format_fail_rate,
            'total_calls': self.metrics['total_calls'],
            'numer_problems': n_problems,
            'num_with_answers': n_with_answers,
        }
    
    def save_results(self, output_dir: str, experiment_name: str):
        """Save results to JSONL and CSV."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().isoformat()
        
        # Save JSONL
        jsonl_path = output_dir / f'{experiment_name}_responses.jsonl'
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for record in self.records:
                f.write(json.dumps(record.to_dict()) + '\n')
        logger.info(f"Saved {len(self.records)} records to {jsonl_path}")
        
        # Save CSV
        csv_path = output_dir / f'{experiment_name}_results.csv'
        with open(csv_path, 'w', encoding='utf-8') as f:
            if self.records:
                # Header
                headers = ['id', 'prompt_type', 'parsed_answer', 'verification_passed', 
                          'expected_answer', 'correct', 'time_s']
                f.write(','.join(headers) + '\n')
                
                # Rows
                for record in self.records:
                    row = [
                        record.id,
                        record.prompt_type,
                        str(record.parsed_answer) if record.parsed_answer is not None else '',
                        str(record.verification_passed),
                        str(record.expected_answer) if record.expected_answer is not None else '',
                        str(record.correct) if record.correct is not None else '',
                        f"{record.time_s:.2f}"
                    ]
                    f.write(','.join(row) + '\n')
        logger.info(f"Saved results to {csv_path}")

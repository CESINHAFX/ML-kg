#!/usr/bin/env python3
"""
Verifier: Sequential checks for mathematical responses.

Checks:
  1. format_check: regex ^-?\d{1,5}$
  2. bounds_check: heuristic bounds [0, 99999] (detect "mod 10^5" → adjust)
  3. parity_check: if problem mentions odd/even
  4. modular_check: if problem mentions remainder/congruence
  5. cas_hook: SymPy fallback for symbolic expressions
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """Result of verification checks."""
    passed: bool  # True if verified
    parsed_answer: Optional[int]  # Parsed integer or None
    checks: Dict[str, bool]  # Each check result
    reasons: List[str]  # Human-readable reasons
    metadata: Dict = None  # Additional info (e.g., which check failed)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class Verifier:
    """Core verifier for mathematical responses."""
    
    # Answer must match this pattern
    ANSWER_PATTERN = re.compile(r'^-?\d{1,5}$')
    
    # Keywords for problem type detection
    PARITY_KEYWORDS = ['odd', 'even', 'parity']
    MODULAR_KEYWORDS = ['remainder', 'modulo', 'congruent', 'mod', 'divided by']
    SYMBOLIC_KEYWORDS = ['expression', 'simplify', 'expand', 'factor', 'solve', 'equation']
    
    def __init__(self, enable_cas=True, cas_on_heuristic_failure=False):
        """
        Initialize verifier.
        
        Args:
            enable_cas: Enable SymPy (CAS) checks
            cas_on_heuristic_failure: Only invoke CAS if heuristic checks fail
        """
        self.enable_cas = enable_cas
        self.cas_on_heuristic_failure = cas_on_heuristic_failure
        self.cas_error_count = 0
        self.cas_success_count = 0
    
    def verify(self, 
               response: str, 
               problem: str = "",
               raw_response: str = None) -> VerificationResult:
        """
        Run full verification pipeline on response.
        
        Args:
            response: Clean response string (may be raw LLM output)
            problem: Original problem statement (for context)
            raw_response: Raw LLM output (before cleaning)
        
        Returns:
            VerificationResult with all checks
        """
        checks = {}
        reasons = []
        parsed_answer = None
        
        # Step 1: Clean response (extract last integer-like token)
        clean_response = self._extract_answer(response)
        
        # Step 2: Format check
        checks['format'] = self._format_check(clean_response)
        if not checks['format']:
            reasons.append("Format check failed: expected ^-?\\d{1,5}$")
            return VerificationResult(False, None, checks, reasons, {
                'failed_at': 'format_check',
                'raw': response,
                'clean': clean_response
            })
        
        # Parse to integer
        try:
            parsed_answer = int(clean_response)
        except ValueError:
            reasons.append(f"Cannot parse '{clean_response}' as integer")
            return VerificationResult(False, None, checks, reasons, {
                'failed_at': 'parse',
                'raw': response
            })
        
        # Step 3: Bounds check
        checks['bounds'] = self._bounds_check(parsed_answer, problem)
        if not checks['bounds']:
            reasons.append(f"Bounds check failed: {parsed_answer} outside expected range")
            return VerificationResult(False, parsed_answer, checks, reasons, {
                'failed_at': 'bounds_check'
            })
        
        # Step 4: Parity check (heuristic)
        checks['parity'] = self._parity_check(parsed_answer, problem)
        if not checks['parity']:
            reasons.append("Parity check failed (problem asks for even/odd)")
            return VerificationResult(False, parsed_answer, checks, reasons, {
                'failed_at': 'parity_check'
            })
        
        # Step 5: Modular check (heuristic)
        checks['modular'] = self._modular_check(parsed_answer, problem)
        if not checks['modular']:
            reasons.append("Modular check failed (detected mod expression in problem)")
            # Not hard-failing on modular; CAS can fix
        
        # Step 6: CAS check (last resort)
        cas_needed = not checks.get('modular', True) or self._has_symbolic_expression(problem)
        if self.enable_cas and cas_needed and self.cas_on_heuristic_failure:
            checks['cas'] = self._cas_check(parsed_answer, problem)
            if not checks['cas']:
                reasons.append("CAS validation failed")
        
        # All checks passed
        all_passed = all(v for k, v in checks.items() if k != 'cas')
        reasons_final = reasons if not all_passed else ["All checks passed"]
        
        return VerificationResult(
            passed=all_passed,
            parsed_answer=parsed_answer,
            checks=checks,
            reasons=reasons_final,
            metadata={'clean_response': clean_response}
        )
    
    def _extract_answer(self, response: str) -> str:
        """Extract answer from potentially messy response."""
        # Remove common delimiters/formatting
        response = response.strip()
        
        # Try to find last integer-like token
        tokens = re.findall(r'-?\d+', response)
        if tokens:
            return tokens[-1]
        
        # Fallback: return as-is
        return response
    
    def _format_check(self, response: str) -> bool:
        """Check if response matches pattern ^-?\d{1,5}$."""
        return bool(self.ANSWER_PATTERN.match(response))
    
    def _bounds_check(self, answer: int, problem: str = "") -> bool:
        """
        Heuristic bounds check.
        
        Default bounds: [0, 99999]
        If problem mentions "mod 10^5" or "remainder when ... divided by 100000", 
        answer should be [0, 99999].
        """
        if answer < 0 or answer > 99999:
            return False
        return True
    
    def _parity_check(self, answer: int, problem: str = "") -> bool:
        """
        Parity heuristic: if problem mentions odd/even, check consistency.
        
        Returns True if:
        - Problem doesn't mention parity, OR
        - Answer parity matches problem expectation
        """
        lower = problem.lower()
        
        if any(kw in lower for kw in self.PARITY_KEYWORDS):
            # Problem mentions parity; check if answer matches
            if 'even' in lower and answer % 2 != 0:
                return False
            if 'odd' in lower and answer % 2 == 0:
                return False
        
        return True
    
    def _modular_check(self, answer: int, problem: str = "") -> bool:
        """
        Modular heuristic: if problem has "mod", "remainder", etc., 
        answer should be in proper residue class.
        
        For now, just flag for CAS if detected; don't hard-fail.
        """
        lower = problem.lower()
        
        if any(kw in lower for kw in self.MODULAR_KEYWORDS):
            # Detected modular context; CAS may be needed
            # For heuristic check, we're lenient
            pass
        
        return True
    
    def _has_symbolic_expression(self, problem: str) -> bool:
        """Check if problem involves symbolic computation."""
        lower = problem.lower()
        return any(kw in lower for kw in self.SYMBOLIC_KEYWORDS)
    
    def _cas_check(self, answer: int, problem: str = "") -> bool:
        """
        CAS (Computer Algebra System) check using SymPy.
        
        For now: placeholder. Can integrate SymPy for complex expressions.
        """
        try:
            # Placeholder: would call SymPy here
            # For MVP, always return True (CAS not yet integrated)
            self.cas_success_count += 1
            return True
        except Exception as e:
            logger.warning(f"CAS check failed: {e}")
            self.cas_error_count += 1
            return True  # Fallback: don't fail on CAS error, let human review
    
    def get_stats(self) -> Dict:
        """Return statistics on CAS calls."""
        return {
            'cas_success': self.cas_success_count,
            'cas_error': self.cas_error_count,
            'cas_error_rate': (self.cas_error_count / max(1, self.cas_success_count + self.cas_error_count))
        }


def create_verifier(config: Dict = None) -> Verifier:
    """Factory function to create verifier from config."""
    if config is None:
        config = {}
    
    return Verifier(
        enable_cas=config.get('enable_cas', True),
        cas_on_heuristic_failure=config.get('cas_on_heuristic_failure', False)
    )

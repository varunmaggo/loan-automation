"""Evaluation metrics for the loan triage system."""

import json
from typing import Any, Dict, List

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class PolicyComplianceMetric(BaseMetric):
    """Metric to check if decisions comply with lending policy."""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self._name = "PolicyComplianceMetric"

    def __name__(self) -> str:
        return self._name

    def measure(self, test_case: LLMTestCase) -> float:
        """Measure policy compliance."""
        # Parse actual output
        try:
            actual = json.loads(test_case.actual_output)
        except json.JSONDecodeError:
            return 0.0
        
        # Check policy rules
        compliance_score = self._check_policy(actual)
        
        self.success = compliance_score >= self.threshold
        return compliance_score

    def _check_policy(self, decision: Dict[str, Any]) -> float:
        """Check if decision complies with policy rules."""
        score = 0.0
        total_checks = 0
        
        # Rule 1: Must have valid recommendation
        total_checks += 1
        if decision.get("recommendation") in ["approve", "reject", "human_review", "approve_fast_track"]:
            score += 1.0
        
        # Rule 2: Must have valid status
        total_checks += 1
        if decision.get("status") in ["approved", "rejected", "human_review", "approved_fast_track"]:
            score += 1.0
        
        # Rule 3: Must have valid risk band
        total_checks += 1
        if decision.get("risk_band") in ["prime", "near_prime", "high_risk"]:
            score += 1.0
        
        # Rule 4: Must have reasons for decision
        total_checks += 1
        if decision.get("reasons") and len(decision.get("reasons", [])) > 0:
            score += 1.0
        
        # Rule 5: Must have application_id
        total_checks += 1
        if decision.get("application_id"):
            score += 1.0
        
        return score / total_checks if total_checks > 0 else 0.0

    def is_successful(self) -> bool:
        """Check if metric passed."""
        return self.success


class SchemaValidityMetric(BaseMetric):
    """Metric to check if output matches expected schema."""

    def __init__(self, threshold: float = 0.90):
        self.threshold = threshold
        self._name = "SchemaValidityMetric"

    def __name__(self) -> str:
        return self._name

    def measure(self, test_case: LLMTestCase) -> float:
        """Measure schema validity."""
        try:
            actual = json.loads(test_case.actual_output)
        except json.JSONDecodeError:
            return 0.0
        
        validity_score = self._check_schema(actual)
        self.success = validity_score >= self.threshold
        return validity_score

    def _check_schema(self, decision: Dict[str, Any]) -> float:
        """Check if decision has required schema fields."""
        score = 0.0
        total_checks = 0
        
        required_fields = [
            "application_id", "recommendation", "status", 
            "risk_band", "reasons", "requires_human_review"
        ]
        
        for field in required_fields:
            total_checks += 1
            if field in decision:
                score += 1.0
        
        # Check nested objects
        total_checks += 1
        if isinstance(decision.get("reasons"), list):
            score += 1.0
        
        return score / total_checks if total_checks > 0 else 0.0

    def is_successful(self) -> bool:
        """Check if metric passed."""
        return self.success


class ExactMatchMetric(BaseMetric):
    """Metric to check for exact match with expected output."""

    def __init__(self, threshold: float = 0.90):
        self.threshold = threshold
        self._name = "ExactMatchMetric"

    def __name__(self) -> str:
        return self._name

    def measure(self, test_case: LLMTestCase) -> float:
        """Measure exact match."""
        try:
            actual = json.loads(test_case.actual_output)
            expected = json.loads(test_case.expected_output)
        except (json.JSONDecodeError, TypeError):
            return 0.0
        
        match_score = self._check_exact_match(actual, expected)
        self.success = match_score >= self.threshold
        return match_score

    def _check_exact_match(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Check exact match between actual and expected."""
        score = 0.0
        total_checks = 0
        
        # Check key fields
        key_fields = ["application_id", "recommendation", "status", "risk_band"]
        
        for field in key_fields:
            total_checks += 1
            if actual.get(field) == expected.get(field):
                score += 1.0
        
        return score / total_checks if total_checks > 0 else 0.0

    def is_successful(self) -> bool:
        """Check if metric passed."""
        return self.success


def slice_disparity(test_cases: List[LLMTestCase]) -> Dict[str, float]:
    """Calculate approval rate disparity across risk bands."""
    # Group by risk band
    approvals_by_band = {}
    total_by_band = {}
    
    for test_case in test_cases:
        try:
            actual = json.loads(test_case.actual_output)
            expected = json.loads(test_case.expected_output)
            
            risk_band = actual.get("risk_band", "unknown")
            
            total_by_band[risk_band] = total_by_band.get(risk_band, 0) + 1
            
            # Check if approved
            if actual.get("recommendation") in ["approve", "approve_fast_track"]:
                approvals_by_band[risk_band] = approvals_by_band.get(risk_band, 0) + 1
                
        except (json.JSONDecodeError, TypeError):
            continue
    
    # Calculate approval rates
    disparity = {}
    for band in total_by_band:
        approval_rate = approvals_by_band.get(band, 0) / total_by_band[band]
        disparity[band] = approval_rate
    
    return disparity

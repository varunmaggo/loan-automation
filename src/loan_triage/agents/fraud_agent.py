"""Fraud detection agent."""

from typing import Any, Dict

from ..schemas import LoanApplication
from ..memory import RunMemory
from .base import BaseAgent


class FraudAgent(BaseAgent):
    """Fraud detection agent."""

    def __init__(self):
        super().__init__(
            name="fraud_agent",
            description="Detects potential fraud in loan applications"
        )

    def process(self, input_data: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Process fraud detection."""
        application = LoanApplication(**input_data)
        
        result = self._detect_fraud(application)
        
        return result

    def _detect_fraud(self, application: LoanApplication) -> Dict[str, Any]:
        """Detect potential fraud."""
        fraud_score = 0.0
        red_flags = []
        
        # Check for suspicious patterns
        if "fraud" in application.applicant_name.lower():
            red_flags.append("Name matches fraud pattern")
            fraud_score += 0.3
        
        if application.loan_amount > 50000:
            red_flags.append("High loan amount")
            fraud_score += 0.1
        
        if application.annual_income < 10000:
            red_flags.append("Unusually low income")
            fraud_score += 0.1
        
        # Determine if fraud risk
        is_fraud_risk = fraud_score > 0.5
        
        return {
            "is_fraud_risk": is_fraud_risk,
            "fraud_score": round(fraud_score, 2),
            "red_flags": red_flags,
            "recommendation": "flag" if is_fraud_risk else "clear"
        }

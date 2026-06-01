"""Credit analysis agent."""

from typing import Any, Dict

from ..schemas import LoanApplication
from ..memory import RunMemory
from .base import BaseAgent


class CreditAgent(BaseAgent):
    """Credit analysis agent."""

    def __init__(self):
        super().__init__(
            name="credit_agent",
            description="Analyzes creditworthiness of applicants"
        )

    def process(self, input_data: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Process credit analysis."""
        application = LoanApplication(**input_data)
        
        result = self._analyze_credit(application)
        
        return result

    def _analyze_credit(self, application: LoanApplication) -> Dict[str, Any]:
        """Analyze creditworthiness."""
        credit_score = application.credit_score
        
        # Determine risk band based on credit score
        if credit_score >= 750:
            risk_band = "prime"
            recommendation = "approve"
        elif credit_score >= 650:
            risk_band = "near_prime"
            recommendation = "approve_with_conditions"
        else:
            risk_band = "high_risk"
            recommendation = "reject"
        
        # Calculate debt-to-income ratio (simplified)
        monthly_income = application.annual_income / 12
        monthly_payment = application.loan_amount / 36  # 3-year term
        dti_ratio = monthly_payment / monthly_income if monthly_income > 0 else 1.0
        
        # Determine if additional conditions needed
        requires_conditions = dti_ratio > 0.36
        
        return {
            "credit_score": credit_score,
            "risk_band": risk_band,
            "dti_ratio": round(dti_ratio, 2),
            "recommendation": recommendation,
            "requires_conditions": requires_conditions,
            "credit_history_years": 5,  # Mock value
            "delinquencies": 0  # Mock value
        }

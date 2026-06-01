"""Decision agent - makes final loan decision."""

import json
from typing import Any, Dict, List

from ..schemas import LoanApplication, RiskBand, TriageDecision
from ..memory import RunMemory
from .base import BaseAgent


class DecisionAgent(BaseAgent):
    """Decision agent that makes final loan decisions."""

    def __init__(self):
        super().__init__(
            name="decision_agent",
            description="Makes final loan approval/rejection decision"
        )

    def process(self, input_data: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Process decision making."""
        application = LoanApplication(**input_data["application"])
        specialist_results = input_data["specialist_results"]
        
        result = self._make_decision(application, specialist_results)
        
        return result

    def _make_decision(
        self,
        application: LoanApplication,
        specialist_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make final loan decision based on all inputs."""
        # Gather inputs from specialists
        kyc_result = specialist_results.get("kyc_agent", {})
        fraud_result = specialist_results.get("fraud_agent", {})
        credit_result = specialist_results.get("credit_agent", {})
        documents_result = specialist_results.get("documents_agent", {})
        
        # Check for any failures
        if not kyc_result.get("verified", False):
            return self._create_rejection("KYC verification failed")
        
        if fraud_result.get("is_fraud_risk", False):
            return self._create_rejection("Fraud risk detected")
        
        if not documents_result.get("documents_verified", False):
            return self._create_rejection("Documents not verified")
        
        # Get credit recommendation
        credit_recommendation = credit_result.get("recommendation", "reject")
        
        if credit_recommendation == "reject":
            return self._create_rejection("Credit not approved")
        
        # Determine final recommendation
        if credit_recommendation == "approve" and credit_result.get("risk_band") == "prime":
            recommendation = "approve_fast_track"
            risk_band = RiskBand.PRIME
        elif credit_recommendation == "approve_with_conditions":
            recommendation = "approve"
            risk_band = RiskBand.NEAR_PRIME
        else:
            recommendation = "human_review"
            risk_band = RiskBand.HIGH_RISK
        
        # Generate reasons
        reasons = self._generate_reasons(
            application, credit_result, specialist_results
        )
        
        return {
            "recommendation": recommendation,
            "risk_band": risk_band,
            "reasons": reasons,
            "requires_human_review": recommendation == "human_review",
            "required_documents": documents_result.get("required_documents", [])
        }

    def _create_rejection(self, reason: str) -> Dict[str, Any]:
        """Create a rejection decision."""
        return {
            "recommendation": "reject",
            "risk_band": "high_risk",
            "reasons": [reason],
            "requires_human_review": False,
            "required_documents": []
        }

    def _generate_reasons(
        self,
        application: LoanApplication,
        credit_result: Dict[str, Any],
        specialist_results: Dict[str, Any]
    ) -> List[str]:
        """Generate decision reasons."""
        reasons = []
        
        # Positive factors
        if credit_result.get("credit_score", 0) >= 750:
            reasons.append("Excellent credit score")
        
        if credit_result.get("dti_ratio", 1.0) < 0.30:
            reasons.append("Low debt-to-income ratio")
        
        if specialist_results.get("kyc_agent", {}).get("verified", False):
            reasons.append("Identity verified")
        
        if not specialist_results.get("fraud_agent", {}).get("is_fraud_risk", False):
            reasons.append("No fraud indicators")
        
        # Risk factors
        if credit_result.get("dti_ratio", 0) > 0.36:
            reasons.append("High debt-to-income ratio")
        
        if application.loan_amount > 50000:
            reasons.append("Large loan amount requires monitoring")
        
        return reasons

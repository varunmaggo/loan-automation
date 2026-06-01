"""KYC (Know Your Customer) agent."""

from typing import Any, Dict

from ..schemas import LoanApplication
from ..memory import RunMemory
from .base import BaseAgent


class KYCAgent(BaseAgent):
    """KYC agent responsible for identity verification."""

    def __init__(self):
        super().__init__(
            name="kyc_agent",
            description="Verifies applicant identity and address"
        )

    def process(self, input_data: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Process KYC verification."""
        application = LoanApplication(**input_data)
        
        # Simulate KYC checks
        result = self._perform_kyc_checks(application)
        
        return result

    def _perform_kyc_checks(self, application: LoanApplication) -> Dict[str, Any]:
        """Perform KYC verification checks."""
        # In real implementation, this would call external KYC services
        # For now, use deterministic mock logic
        
        # Check if name contains red flags
        name = application.applicant_name.lower()
        red_flags = []
        
        if any(word in name for word in ["test", "demo", "sample"]):
            red_flags.append("Name contains suspicious keywords")
        
        # Verify address format
        address_valid = self._validate_address(application.address)
        
        # Determine verification status
        verified = len(red_flags) == 0 and address_valid
        
        return {
            "verified": verified,
            "confidence": 0.95 if verified else 0.5,
            "issues": red_flags,
            "identity_verified": verified,
            "address_verified": address_valid,
            "recommendation": "clear" if verified else "review"
        }

    def _validate_address(self, address: str) -> bool:
        """Validate address format."""
        # Simple validation - in production, use address verification API
        if not address or len(address) < 5:
            return False
        return True

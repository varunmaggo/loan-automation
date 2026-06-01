"""Documents verification agent."""

from typing import Any, Dict

from ..schemas import LoanApplication
from ..memory import RunMemory
from .base import BaseAgent


class DocumentsAgent(BaseAgent):
    """Documents verification agent."""

    def __init__(self):
        super().__init__(
            name="documents_agent",
            description="Verifies required documents for loan application"
        )

    def process(self, input_data: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Process document verification."""
        application = LoanApplication(**input_data)
        
        result = self._verify_documents(application)
        
        return result

    def _verify_documents(self, application: LoanApplication) -> Dict[str, Any]:
        """Verify required documents."""
        # Determine required documents based on loan amount
        required_documents = self._get_required_documents(application.loan_amount)
        
        # In real implementation, check document management system
        # For mock, assume all documents are provided
        documents_verified = True
        missing_documents = []
        
        return {
            "documents_verified": documents_verified,
            "required_documents": required_documents,
            "missing_documents": missing_documents,
            "recommendation": "complete" if documents_verified else "incomplete"
        }

    def _get_required_documents(self, loan_amount: float) -> list:
        """Get required documents based on loan amount."""
        base_docs = ["identity_proof", "income_proof"]
        
        if loan_amount > 25000:
            base_docs.append("asset_verification")
        
        if loan_amount > 50000:
            base_docs.append("business_plan")
        
        return base_docs

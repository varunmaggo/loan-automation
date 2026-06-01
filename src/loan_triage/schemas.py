"""Data schemas for the loan triage system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LoanApplicationStatus(str, Enum):
    """Status of a loan application."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    HUMAN_REVIEW = "human_review"
    APPROVED_FAST_TRACK = "approved_fast_track"


class RiskBand(str, Enum):
    """Risk classification for loan applicants."""

    PRIME = "prime"
    NEAR_PRIME = "near_prime"
    HIGH_RISK = "high_risk"


class LoanApplication(BaseModel):
    """Loan application input schema."""

    application_id: str = Field(..., description="Unique application ID")
    applicant_name: str = Field(..., description="Applicant full name")
    applicant_email: str = Field(..., description="Applicant email address")
    applicant_phone: str = Field(..., description="Applicant phone number")
    loan_amount: float = Field(..., ge=1000, le=100000, description="Requested loan amount")
    loan_purpose: str = Field(..., description="Purpose of the loan")
    credit_score: int = Field(..., ge=300, le=850, description="Applicant credit score")
    annual_income: float = Field(..., ge=0, description="Applicant annual income")
    employment_status: str = Field(..., description="Current employment status")
    address: str = Field(..., description="Applicant address")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(BaseModel):
    """Message envelope for agent communication."""

    message_id: str = Field(..., description="Unique message ID")
    sender: str = Field(..., description="Sender agent name")
    recipient: str = Field(..., description="Recipient agent name")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = Field(None, description="HMAC-SHA256 signature")


class TriageDecision(BaseModel):
    """Final triage decision output."""

    application_id: str = Field(..., description="Associated application ID")
    recommendation: str = Field(..., description="Recommendation (approve/reject/human_review)")
    status: LoanApplicationStatus = Field(..., description="Final status")
    risk_band: RiskBand = Field(..., description="Assigned risk band")
    reasons: List[str] = Field(default_factory=list, description="Decision reasons")
    required_documents: List[str] = Field(default_factory=list, description="Required documents")
    requires_human_review: bool = Field(default=False, description="Requires human review flag")
    estimated_processing_days: int = Field(default=3, description="Estimated processing time")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentRun(BaseModel):
    """Run metadata and results."""

    run_id: str = Field(..., description="Unique run ID")
    application_id: str = Field(..., description="Associated application ID")
    decision: TriageDecision = Field(..., description="Final decision")
    messages: List[AgentMessage] = Field(default_factory=list, description="Message history")
    tool_outputs: List[Dict[str, Any]] = Field(default_factory=list, description="Tool call results")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(None, description="Run completion time")
    total_cost_usd: float = Field(default=0.0, description="Total LLM cost")
    total_tool_calls: int = Field(default=0, description="Total tool calls made")


class ToolCall(BaseModel):
    """Tool call request."""

    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    tool_call_id: str = Field(..., description="Unique tool call ID")


class ToolResponse(BaseModel):
    """Tool call response."""

    tool_call_id: str = Field(..., description="Associated tool call ID")
    tool_name: str = Field(..., description="Name of the tool")
    success: bool = Field(..., description="Whether the call succeeded")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool result data")
    error: Optional[str] = Field(None, description="Error message if failed")

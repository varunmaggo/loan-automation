"""Tests for loan triage agents."""

import json
import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loan_triage.schemas import (
    LoanApplication, TriageDecision, AgentMessage
)
from loan_triage.memory import RunMemory
from loan_triage.agents.orchestrator import Orchestrator
from loan_triage.agents.kyc_agent import KYCAgent
from loan_triage.agents.fraud_agent import FraudAgent
from loan_triage.agents.credit_agent import CreditAgent
from loan_triage.agents.documents_agent import DocumentsAgent
from loan_triage.agents.decision_agent import DecisionAgent


@pytest.fixture
def sample_application():
    """Create a sample loan application."""
    return LoanApplication(
        application_id="app_001",
        applicant_name="John Doe",
        applicant_email="john@example.com",
        applicant_phone="555-1234",
        loan_amount=25000,
        loan_purpose="home_improvement",
        credit_score=750,
        annual_income=75000,
        employment_status="employed",
        address="123 Main St, City, State 12345"
    )


@pytest.fixture
def memory():
    """Create a run memory instance."""
    return RunMemory(
        run_id="test_run_001",
        application_id="app_001"
    )


class TestKYCAgent:
    """Tests for KYC agent."""

    def test_kyc_agent_processes_application(self, sample_application, memory):
        """Test KYC agent processes a valid application."""
        agent = KYCAgent()
        result = agent.process(sample_application.model_dump(), memory)
        
        assert "verified" in result
        assert "recommendation" in result

    def test_kyc_agent_detects_suspicious_name(self, memory):
        """Test KYC agent detects suspicious names."""
        app = LoanApplication(
            application_id="app_002",
            applicant_name="Test User",
            applicant_email="test@example.com",
            applicant_phone="555-1234",
            loan_amount=25000,
            loan_purpose="home_improvement",
            credit_score=750,
            annual_income=75000,
            employment_status="employed",
            address="123 Main St, City, State 12345"
        )
        
        agent = KYCAgent()
        result = agent.process(app.model_dump(), memory)
        
        # Should have issues for suspicious name
        assert "issues" in result


class TestFraudAgent:
    """Tests for fraud detection agent."""

    def test_fraud_agent_processes_application(self, sample_application, memory):
        """Test fraud agent processes a valid application."""
        agent = FraudAgent()
        result = agent.process(sample_application.model_dump(), memory)
        
        assert "is_fraud_risk" in result
        assert "fraud_score" in result
        assert "recommendation" in result

    def test_fraud_agent_detects_high_amount(self, memory):
        """Test fraud agent flags high loan amounts."""
        app = LoanApplication(
            application_id="app_003",
            applicant_name="Jane Smith",
            applicant_email="jane@example.com",
            applicant_phone="555-1234",
            loan_amount=75000,  # High amount
            loan_purpose="home_improvement",
            credit_score=750,
            annual_income=75000,
            employment_status="employed",
            address="123 Main St, City, State 12345"
        )
        
        agent = FraudAgent()
        result = agent.process(app.model_dump(), memory)
        
        # May flag high amount
        assert "red_flags" in result


class TestCreditAgent:
    """Tests for credit analysis agent."""

    def test_credit_agent_processes_application(self, sample_application, memory):
        """Test credit agent processes a valid application."""
        agent = CreditAgent()
        result = agent.process(sample_application.model_dump(), memory)
        
        assert "credit_score" in result
        assert "risk_band" in result
        assert "recommendation" in result

    def test_credit_agent_determines_risk_band(self, memory):
        """Test credit agent determines correct risk band."""
        app = LoanApplication(
            application_id="app_004",
            applicant_name="Bob Wilson",
            applicant_email="bob@example.com",
            applicant_phone="555-1234",
            loan_amount=25000,
            loan_purpose="home_improvement",
            credit_score=600,  # Lower score
            annual_income=50000,
            employment_status="employed",
            address="123 Main St, City, State 12345"
        )
        
        agent = CreditAgent()
        result = agent.process(app.model_dump(), memory)
        
        # Should be near_prime or high_risk
        assert result["risk_band"] in ["near_prime", "high_risk"]


class TestDocumentsAgent:
    """Tests for documents verification agent."""

    def test_documents_agent_processes_application(self, sample_application, memory):
        """Test documents agent processes a valid application."""
        agent = DocumentsAgent()
        result = agent.process(sample_application.model_dump(), memory)
        
        assert "documents_verified" in result
        assert "required_documents" in result
        assert "recommendation" in result


class TestDecisionAgent:
    """Tests for decision agent."""

    def test_decision_agent_processes_full_input(self, sample_application, memory):
        """Test decision agent processes complete input."""
        specialist_results = {
            "kyc_agent": {"verified": True, "confidence": 0.95, "issues": []},
            "fraud_agent": {"is_fraud_risk": False, "fraud_score": 0.1, "red_flags": []},
            "credit_agent": {
                "credit_score": 750,
                "risk_band": "prime",
                "recommendation": "approve",
                "dti_ratio": 0.25
            },
            "documents_agent": {"documents_verified": True, "missing_documents": []}
        }
        
        input_data = {
            "application": sample_application.model_dump(),
            "specialist_results": specialist_results
        }
        
        agent = DecisionAgent()
        result = agent.process(input_data, memory)
        
        assert "recommendation" in result
        assert "risk_band" in result
        assert "reasons" in result


class TestOrchestrator:
    """Tests for orchestrator agent."""

    def test_orchestrator_coordinates_agents(self, sample_application, memory):
        """Test orchestrator coordinates all agents."""
        orchestrator = Orchestrator()
        result = orchestrator.process(sample_application.model_dump(), memory)
        
        assert "decision" in result
        assert "messages" in result
        assert "tool_outputs" in result
        
        decision = result["decision"]
        assert "recommendation" in decision
        assert "status" in decision

    def test_orchestrator_records_messages(self, sample_application, memory):
        """Test orchestrator records message history."""
        orchestrator = Orchestrator()
        result = orchestrator.process(sample_application.model_dump(), memory)
        
        # Should have messages for each agent interaction
        assert len(memory.messages) > 0


class TestSchemas:
    """Tests for data schemas."""

    def test_loan_application_schema(self):
        """Test loan application schema validation."""
        app = LoanApplication(
            application_id="app_001",
            applicant_name="John Doe",
            applicant_email="john@example.com",
            applicant_phone="555-1234",
            loan_amount=25000,
            loan_purpose="home_improvement",
            credit_score=750,
            annual_income=75000,
            employment_status="employed",
            address="123 Main St, City, State 12345"
        )
        
        assert app.application_id == "app_001"
        assert app.loan_amount == 25000

    def test_triage_decision_schema(self):
        """Test triage decision schema validation."""
        decision = TriageDecision(
            application_id="app_001",
            recommendation="approve",
            status="approved",
            risk_band="prime",
            reasons=["Good credit score"],
            requires_human_review=False
        )
        
        assert decision.recommendation == "approve"
        assert decision.risk_band == "prime"


class TestMemory:
    """Tests for run memory."""

    def test_memory_records_tool_outputs(self, memory):
        """Test memory records tool call results."""
        from src.loan_triage.schemas import ToolCall, ToolResponse
        
        tool_call = ToolCall(
            tool_name="check_fraud_database",
            parameters={},
            tool_call_id="tool_001"
        )
        
        response = ToolResponse(
            tool_call_id="tool_001",
            tool_name="check_fraud_database",
            success=True,
            result={"is_fraud_risk": False}
        )
        
        memory.add_tool_output(tool_call, response)
        
        assert len(memory.tool_outputs) == 1
        assert memory.total_tool_calls == 1

    def test_memory_records_cost(self, memory):
        """Test memory tracks costs."""
        memory.add_cost(0.001)
        memory.add_cost(0.002)
        
        assert memory.total_cost_usd == 0.003

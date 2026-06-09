"""
Unit tests for specialist agents.

Each agent is tested independently with deterministic inputs —
this is the key advantage of fleet architecture over a monolith.
Run with:  pytest tests/
"""

import pytest
from agents.specialists import CreditAgent, DocumentsAgent, FraudAgent, KYCAgent


# ─── KYC Agent ────────────────────────────────────────────────────────────────

class TestKYCAgent:
    def setup_method(self):
        self.agent = KYCAgent()

    def test_valid_applicant(self):
        result = self.agent.run({
            "name": "John Doe",
            "ssn": "123-45-6789",
            "address": "123 Main St",
        })
        assert result["verified"] is True
        assert result["score"] == 1.0
        assert result["errors"] == []

    def test_invalid_ssn_format(self):
        result = self.agent.run({
            "name": "John Doe",
            "ssn": "INVALID",
            "address": "123 Main St",
        })
        assert result["verified"] is False
        assert any("SSN" in e for e in result["errors"])

    def test_missing_name(self):
        result = self.agent.run({
            "name": "",
            "ssn": "123-45-6789",
            "address": "123 Main St",
        })
        assert result["verified"] is False
        assert any("Name" in e for e in result["errors"])

    def test_missing_address(self):
        result = self.agent.run({
            "name": "John Doe",
            "ssn": "123-45-6789",
            "address": "",
        })
        assert result["verified"] is False

    def test_score_reflects_partial_validity(self):
        # Each test gets a fresh agent via setup_method, so budget is clean
        result = KYCAgent().run({
            "name": "John Doe",
            "ssn": "BAD",       # fails
            "address": "123 Main St",
        })
        assert result["score"] == pytest.approx(2 / 3, abs=0.01)


# ─── Fraud Agent ──────────────────────────────────────────────────────────────

class TestFraudAgent:
    def setup_method(self):
        self.agent = FraudAgent()

    def test_clean_applicant(self):
        result = self.agent.run({
            "ssn": "123-45-6789",
            "loan_amount": 50_000,
            "applications_last_30_days": 0,
        })
        assert result["risk_level"] == "low"
        assert result["risk_score"] == 0.0
        assert result["flags"] == []

    def test_blocklisted_ssn(self):
        result = self.agent.run({
            "ssn": "000-00-0000",
            "loan_amount": 50_000,
            "applications_last_30_days": 0,
        })
        assert result["risk_score"] == 1.0
        assert result["risk_level"] == "high"
        assert any("blocklist" in f.lower() for f in result["flags"])

    def test_high_loan_amount(self):
        result = self.agent.run({
            "ssn": "123-45-6789",
            "loan_amount": 600_000,
            "applications_last_30_days": 0,
        })
        assert result["risk_score"] >= 0.3
        assert any("loan amount" in f.lower() for f in result["flags"])

    def test_high_velocity(self):
        result = self.agent.run({
            "ssn": "123-45-6789",
            "loan_amount": 50_000,
            "applications_last_30_days": 5,
        })
        assert result["risk_score"] >= 0.4
        assert any("velocity" in f.lower() for f in result["flags"])

    def test_risk_score_capped_at_one(self):
        result = self.agent.run({
            "ssn": "000-00-0000",   # +1.0
            "loan_amount": 600_000,  # +0.3
            "applications_last_30_days": 5,  # +0.4
        })
        assert result["risk_score"] == 1.0


# ─── Credit Agent ─────────────────────────────────────────────────────────────

class TestCreditAgent:
    def setup_method(self):
        self.agent = CreditAgent()

    def test_excellent_credit(self):
        result = self.agent.run({
            "credit_score": 800,
            "monthly_income": 10_000,
            "monthly_debt": 2_000,
        })
        assert result["grade"] == "excellent"
        assert result["eligible"] is True
        assert result["dti_ratio"] == pytest.approx(0.2)

    def test_poor_credit_ineligible(self):
        result = self.agent.run({
            "credit_score": 550,
            "monthly_income": 5_000,
            "monthly_debt": 1_500,
        })
        assert result["grade"] == "poor"
        assert result["eligible"] is False

    def test_dti_too_high(self):
        result = self.agent.run({
            "credit_score": 720,
            "monthly_income": 5_000,
            "monthly_debt": 2_500,  # DTI = 0.50, above 0.43
        })
        assert result["eligible"] is False
        assert result["dti_ratio"] == pytest.approx(0.5)

    def test_fair_credit_low_dti_eligible(self):
        result = self.agent.run({
            "credit_score": 660,
            "monthly_income": 8_000,
            "monthly_debt": 2_000,  # DTI = 0.25
        })
        assert result["eligible"] is True
        assert result["grade"] == "fair"


# ─── Documents Agent ──────────────────────────────────────────────────────────

class TestDocumentsAgent:
    def setup_method(self):
        self.agent = DocumentsAgent()

    def test_all_documents_present(self):
        result = self.agent.run({
            "documents": ["pay_stub", "bank_statement", "government_id", "proof_of_address"],
        })
        assert result["complete"] is True
        assert result["missing"] == []

    def test_missing_document(self):
        result = self.agent.run({
            "documents": ["pay_stub", "bank_statement", "government_id"],
            # missing: proof_of_address
        })
        assert result["complete"] is False
        assert "proof_of_address" in result["missing"]

    def test_no_documents(self):
        result = self.agent.run({"documents": []})
        assert result["complete"] is False
        assert len(result["missing"]) == 4

    def test_extra_documents_ignored(self):
        result = self.agent.run({
            "documents": [
                "pay_stub", "bank_statement", "government_id",
                "proof_of_address", "extra_letter",  # extra is fine
            ],
        })
        assert result["complete"] is True

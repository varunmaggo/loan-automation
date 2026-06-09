"""Tests for base infrastructure: message signing, budget enforcement, PII redaction."""

import pytest
from agents.base import Budget, BudgetExceeded, Message, redact_pii


class TestMessageSigning:
    def test_valid_signature(self):
        msg = Message(sender="orchestrator", recipient="kyc_agent", payload={"action": "verify"})
        assert msg.verify() is True

    def test_tampered_payload_fails_verification(self):
        msg = Message(sender="orchestrator", recipient="kyc_agent", payload={"action": "verify"})
        msg.payload["action"] = "tampered"  # mutate after signing
        assert msg.verify() is False

    def test_message_has_unique_id(self):
        m1 = Message(sender="a", recipient="b", payload={})
        m2 = Message(sender="a", recipient="b", payload={})
        assert m1.message_id != m2.message_id


class TestBudgetEnforcement:
    def test_within_budget(self):
        budget = Budget(max_tool_calls=3, max_wallclock_seconds=10, max_cost_usd=1.0)
        budget.charge(0.01)
        budget.charge(0.01)
        # No exception — within limits

    def test_tool_call_limit_exceeded(self):
        budget = Budget(max_tool_calls=2, max_wallclock_seconds=10, max_cost_usd=1.0)
        budget.charge()
        budget.charge()
        with pytest.raises(BudgetExceeded, match="Tool call limit"):
            budget.charge()

    def test_cost_limit_exceeded(self):
        budget = Budget(max_tool_calls=10, max_wallclock_seconds=10, max_cost_usd=0.05)
        with pytest.raises(BudgetExceeded, match="Cost limit"):
            budget.charge(0.10)


class TestPIIRedaction:
    def test_ssn_redacted(self):
        assert "[REDACTED_SSN]" in redact_pii("SSN: 123-45-6789")

    def test_email_redacted(self):
        assert "[REDACTED_EMAIL]" in redact_pii("Contact: user@example.com")

    def test_phone_redacted(self):
        assert "[REDACTED_PHONE]" in redact_pii("Call: 555-123-4567")

    def test_no_false_positives(self):
        clean = "Score: 750, DTI: 0.35"
        assert redact_pii(clean) == clean

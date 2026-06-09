"""
Specialist agents — all deterministic, no LLM calls.

KYC     → identity verification via pattern matching
Fraud   → rule-based risk scoring
Credit  → score thresholds + debt-to-income ratio
Documents → required-documents checklist
"""

from __future__ import annotations

import re
from typing import Any

from agents.base import BaseAgent


# ─── KYC Agent ────────────────────────────────────────────────────────────────

SSN_PATTERN = re.compile(r"^\d{3}-\d{2}-\d{4}$")


class KYCAgent(BaseAgent):
    name = "kyc_agent"

    def __init__(self) -> None:
        super().__init__(max_tool_calls=2, max_wallclock_seconds=10, max_cost_usd=0.05)

    def _run(self, applicant: dict) -> dict:
        errors: list[str] = []

        # SSN format check
        ssn = applicant.get("ssn", "")
        ssn_valid = bool(SSN_PATTERN.match(ssn))
        if not ssn_valid:
            errors.append(f"Invalid SSN format: {ssn!r}")

        # Name presence
        name = applicant.get("name", "").strip()
        if not name:
            errors.append("Name is missing")

        # Address presence
        address = applicant.get("address", "").strip()
        if not address:
            errors.append("Address is missing")

        # Naive similarity score: how many fields passed / total fields
        fields_checked = 3
        fields_passed = sum([ssn_valid, bool(name), bool(address)])
        score = round(fields_passed / fields_checked, 2)

        return {
            "agent": self.name,
            "verified": len(errors) == 0,
            "score": score,
            "errors": errors,
        }


# ─── Fraud Agent ──────────────────────────────────────────────────────────────

class FraudAgent(BaseAgent):
    name = "fraud_agent"

    # Hardcoded blocklist — in production this would be a DB lookup
    _BLOCKED_SSNS: set[str] = {"000-00-0000", "999-99-9999"}

    def __init__(self) -> None:
        super().__init__(max_tool_calls=3, max_wallclock_seconds=10, max_cost_usd=0.05)

    def _run(self, applicant: dict) -> dict:
        risk_score = 0.0
        flags: list[str] = []

        # Blocklist check (highest weight)
        if applicant.get("ssn") in self._BLOCKED_SSNS:
            risk_score += 1.0
            flags.append("SSN on fraud blocklist")

        # High loan amount
        loan_amount = applicant.get("loan_amount", 0)
        if loan_amount > 500_000:
            risk_score += 0.3
            flags.append(f"High loan amount: ${loan_amount:,}")

        # Velocity: too many recent applications
        recent_apps = applicant.get("applications_last_30_days", 0)
        if recent_apps >= 3:
            risk_score += 0.4
            flags.append(f"High application velocity: {recent_apps} in 30 days")

        risk_score = min(round(risk_score, 2), 1.0)
        risk_level = "high" if risk_score >= 0.7 else ("medium" if risk_score >= 0.3 else "low")

        return {
            "agent": self.name,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags": flags,
        }


# ─── Credit Agent ─────────────────────────────────────────────────────────────

class CreditAgent(BaseAgent):
    name = "credit_agent"

    DTI_MAX = 0.43  # Qualified Mortgage ceiling

    def __init__(self) -> None:
        super().__init__(max_tool_calls=2, max_wallclock_seconds=10, max_cost_usd=0.05)

    def _run(self, applicant: dict) -> dict:
        score = applicant.get("credit_score", 0)
        monthly_income = applicant.get("monthly_income", 1)  # avoid div-by-zero
        monthly_debt = applicant.get("monthly_debt", 0)
        dti = round(monthly_debt / monthly_income, 3) if monthly_income > 0 else 1.0

        if score >= 750:
            grade = "excellent"
        elif score >= 700:
            grade = "good"
        elif score >= 650:
            grade = "fair"
        else:
            grade = "poor"

        eligible = score >= 650 and dti <= self.DTI_MAX

        return {
            "agent": self.name,
            "credit_score": score,
            "grade": grade,
            "dti_ratio": dti,
            "dti_max": self.DTI_MAX,
            "eligible": eligible,
        }


# ─── Documents Agent ──────────────────────────────────────────────────────────

REQUIRED_DOCS = {"pay_stub", "bank_statement", "government_id", "proof_of_address"}


class DocumentsAgent(BaseAgent):
    name = "documents_agent"

    def __init__(self) -> None:
        super().__init__(max_tool_calls=2, max_wallclock_seconds=10, max_cost_usd=0.05)

    def _run(self, applicant: dict) -> dict:
        submitted = set(applicant.get("documents", []))
        missing = sorted(REQUIRED_DOCS - submitted)

        return {
            "agent": self.name,
            "complete": len(missing) == 0,
            "submitted": sorted(submitted),
            "missing": missing,
        }

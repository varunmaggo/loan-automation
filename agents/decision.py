"""
Decision Agent — the ONLY LLM call in the fleet.

Receives aggregated specialist outputs and produces a final recommendation
(APPROVE_FAST_TRACK, APPROVE, HUMAN_REVIEW, REJECT) with reasoning.

Falls back to rule-based fast-track logic when OPENAI_API_KEY is not set,
so the demo runs fully offline with deterministic output.
"""

from __future__ import annotations

import json
import os

from agents.base import BaseAgent


class DecisionAgent(BaseAgent):
    name = "decision_agent"

    def __init__(self) -> None:
        super().__init__(max_tool_calls=1, max_wallclock_seconds=10, max_cost_usd=0.05)

    def _run(self, aggregated: dict) -> dict:  # type: ignore[override]
        kyc = aggregated["kyc"]
        fraud = aggregated["fraud"]
        credit = aggregated["credit"]
        docs = aggregated["documents"]

        # Fast-path rule: deterministic fast-track (no LLM needed)
        if (
            kyc["verified"]
            and kyc["score"] >= 0.90
            and fraud["risk_score"] <= 0.20
            and credit["credit_score"] >= 750
            and docs["complete"]
        ):
            return {
                "agent": self.name,
                "decision": "APPROVE_FAST_TRACK",
                "confidence": 1.0,
                "reasoning": (
                    "All checks passed with high confidence: identity verified, "
                    "fraud risk low, credit excellent, all documents present."
                ),
                "llm_used": False,
            }

        # Auto-reject path: deterministic
        if not kyc["verified"] or fraud["risk_score"] >= 0.70 or credit["credit_score"] < 580:
            reasons = []
            if not kyc["verified"]:
                reasons.append("identity verification failed")
            if fraud["risk_score"] >= 0.70:
                reasons.append(f"high fraud risk ({fraud['risk_score']})")
            if credit["credit_score"] < 580:
                reasons.append(f"credit score too low ({credit['credit_score']})")
            return {
                "agent": self.name,
                "decision": "REJECT",
                "confidence": 1.0,
                "reasoning": "Auto-rejected: " + "; ".join(reasons),
                "llm_used": False,
            }

        # Ambiguous cases: use LLM if key is available, else human review
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return self._llm_decision(aggregated, api_key)

        # No API key — default to human review
        return {
            "agent": self.name,
            "decision": "HUMAN_REVIEW",
            "confidence": 0.5,
            "reasoning": (
                "Application requires human review. "
                "(Set OPENAI_API_KEY to enable LLM-assisted reasoning for borderline cases.)"
            ),
            "llm_used": False,
        }

    def _llm_decision(self, aggregated: dict, api_key: str) -> dict:
        """Call GPT-4o-mini for borderline cases."""
        try:
            from openai import OpenAI  # optional dependency
        except ImportError:
            return {
                "agent": self.name,
                "decision": "HUMAN_REVIEW",
                "confidence": 0.5,
                "reasoning": "openai package not installed; defaulting to human review.",
                "llm_used": False,
            }

        client = OpenAI(api_key=api_key)
        prompt = f"""You are a loan underwriting decision engine.
Given these specialist agent results, output a JSON object with:
  "decision": one of APPROVE | HUMAN_REVIEW | REJECT
  "confidence": float 0.0–1.0
  "reasoning": one-sentence explanation

Specialist results:
{json.dumps(aggregated, indent=2)}

Respond with raw JSON only. No markdown, no extra text."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        result["agent"] = self.name
        result["llm_used"] = True
        return result

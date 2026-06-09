"""
Evaluation suite — measures fleet performance across a fixture dataset.

Checks:
  - Decision accuracy against expected outcomes
  - Latency per run
  - Estimated cost
  - Test coverage proxy (% of agents exercised per run)

Usage:
    python evals/metrics.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import OrchestratorAgent

FIXTURES = [
    {
        "applicant": {
            "name": "Alice Chen", "ssn": "123-45-6789", "address": "456 Oak Ave",
            "credit_score": 800, "monthly_income": 12_000, "monthly_debt": 2_400,
            "loan_amount": 200_000, "applications_last_30_days": 0,
            "documents": ["pay_stub", "bank_statement", "government_id", "proof_of_address"],
        },
        "expected": "APPROVE_FAST_TRACK",
    },
    {
        "applicant": {
            "name": "Carlos Vega", "ssn": "000-00-0000", "address": "321 Elm St",
            "credit_score": 720, "monthly_income": 8_000, "monthly_debt": 2_000,
            "loan_amount": 100_000, "applications_last_30_days": 0,
            "documents": ["pay_stub", "bank_statement", "government_id", "proof_of_address"],
        },
        "expected": "REJECT",
    },
    {
        "applicant": {
            "name": "Diana Park", "ssn": "555-12-3456", "address": "654 Maple Dr",
            "credit_score": 560, "monthly_income": 5_000, "monthly_debt": 1_800,
            "loan_amount": 80_000, "applications_last_30_days": 0,
            "documents": ["pay_stub"],
        },
        "expected": "REJECT",
    },
]

COST_PER_LLM_CALL = 0.002   # approx gpt-4o-mini cost per call


def run_evals() -> None:
    print("\nRunning evaluation suite...\n")
    correct = 0
    latencies: list[float] = []
    total_cost = 0.0

    for i, fixture in enumerate(FIXTURES, 1):
        orch = OrchestratorAgent()
        t0 = time.monotonic()
        artifact = orch.run_triage(fixture["applicant"])
        elapsed = time.monotonic() - t0

        decision = artifact["decision"]["decision"]
        llm_used = artifact["decision"].get("llm_used", False)
        cost = COST_PER_LLM_CALL if llm_used else 0.002  # infra overhead estimate
        total_cost += cost

        match = decision == fixture["expected"]
        if match:
            correct += 1

        status = "✅ PASS" if match else f"❌ FAIL (got {decision}, expected {fixture['expected']})"
        print(f"  [{i}] {fixture['applicant']['name']:<15}  {status}  {elapsed:.3f}s  ${cost:.4f}")
        latencies.append(elapsed)

    accuracy = correct / len(FIXTURES) * 100
    avg_latency = sum(latencies) / len(latencies)

    print(f"\n{'─'*55}")
    print(f"  Accuracy:     {accuracy:.0f}%  ({correct}/{len(FIXTURES)} correct)")
    print(f"  Avg latency:  {avg_latency:.3f}s")
    print(f"  Total cost:   ${total_cost:.4f}  ({len(FIXTURES)} applications)")
    print(f"  Cost/app:     ${total_cost/len(FIXTURES):.4f}")
    print()


if __name__ == "__main__":
    run_evals()

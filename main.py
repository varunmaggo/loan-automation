"""
Loan Triage Fleet — Demo Entry Point

Runs four applicant scenarios through the full fleet to demonstrate
all three decision paths: fast-track approve, human review, and reject.

Usage:
    python main.py
    OPENAI_API_KEY=sk-... python main.py   # enables LLM for borderline cases
"""

import json

from agents.orchestrator import OrchestratorAgent

# ─── Sample Applicants ────────────────────────────────────────────────────────

APPLICANTS = [
    {
        "id": "app_001",
        "label": "Strong applicant — fast-track approve",
        "name": "Alice Chen",
        "ssn": "123-45-6789",
        "address": "456 Oak Ave, Portland, OR",
        "credit_score": 800,
        "monthly_income": 12_000,
        "monthly_debt": 2_400,   # DTI = 0.20
        "loan_amount": 200_000,
        "applications_last_30_days": 0,
        "documents": ["pay_stub", "bank_statement", "government_id", "proof_of_address"],
    },
    {
        "id": "app_002",
        "label": "Borderline — human review or LLM decision",
        "name": "Bob Martinez",
        "ssn": "987-65-4321",
        "address": "789 Pine St, Austin, TX",
        "credit_score": 680,
        "monthly_income": 6_000,
        "monthly_debt": 2_400,   # DTI = 0.40 — within limit but borderline
        "loan_amount": 150_000,
        "applications_last_30_days": 1,
        "documents": ["pay_stub", "bank_statement", "government_id", "proof_of_address"],
    },
    {
        "id": "app_003",
        "label": "Auto-reject — blocklisted SSN",
        "name": "Carlos Vega",
        "ssn": "000-00-0000",    # on fraud blocklist
        "address": "321 Elm St, Miami, FL",
        "credit_score": 720,
        "monthly_income": 8_000,
        "monthly_debt": 2_000,
        "loan_amount": 100_000,
        "applications_last_30_days": 0,
        "documents": ["pay_stub", "bank_statement", "government_id", "proof_of_address"],
    },
    {
        "id": "app_004",
        "label": "Auto-reject — missing documents + poor credit",
        "name": "Diana Park",
        "ssn": "555-12-3456",
        "address": "654 Maple Dr, Chicago, IL",
        "credit_score": 560,
        "monthly_income": 5_000,
        "monthly_debt": 1_800,
        "loan_amount": 80_000,
        "applications_last_30_days": 0,
        "documents": ["pay_stub"],   # missing most documents
    },
]


def main() -> None:
    orchestrator = OrchestratorAgent()
    results = []

    for applicant in APPLICANTS:
        print(f"\n{'─'*60}")
        print(f"  [{applicant['id']}] {applicant['label']}")

        # Fresh orchestrator per run so budgets reset
        orch = OrchestratorAgent()
        artifact = orch.run_triage(applicant)
        artifact["applicant_id"] = applicant["id"]
        results.append(artifact)

    # Summary table
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  {'ID':<10} {'Decision':<22} {'Time':>6}s")
    print(f"  {'-'*10} {'-'*22} {'-'*7}")
    for r in results:
        dec = r["decision"]["decision"]
        elapsed = r["elapsed_seconds"]
        print(f"  {r['applicant_id']:<10} {dec:<22} {elapsed:>6.3f}")

    print()

    # Optionally dump full artifacts to file
    with open("run_artifacts.json", "w") as f:
        json.dump(results, f, indent=2)
    print("  Full artifacts saved to run_artifacts.json\n")


if __name__ == "__main__":
    main()

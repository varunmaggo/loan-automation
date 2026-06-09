"""
Orchestrator Agent — coordinates the fleet and produces a run artifact.

Dispatches specialists, collects results, invokes the Decision Agent,
and assembles a signed, PII-redacted run artifact.
"""

from __future__ import annotations

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from agents.base import BaseAgent, Message, redact_pii
from agents.decision import DecisionAgent
from agents.specialists import CreditAgent, DocumentsAgent, FraudAgent, KYCAgent


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    def __init__(self) -> None:
        super().__init__(max_tool_calls=8, max_wallclock_seconds=30, max_cost_usd=0.25)
        self.kyc = KYCAgent()
        self.fraud = FraudAgent()
        self.credit = CreditAgent()
        self.documents = DocumentsAgent()
        self.decision = DecisionAgent()

    def run_triage(self, applicant: dict) -> dict:
        """
        Full triage pipeline:
          1. Dispatch KYC, Fraud, Credit, Documents in parallel
          2. Collect results
          3. Run Decision Agent
          4. Assemble and return run artifact
        """
        run_id = str(uuid.uuid4())
        started_at = time.time()
        all_messages: list[dict] = []

        print(f"\n{'='*60}")
        print(f"  Loan Triage Fleet — Run {run_id[:8]}")
        print(f"{'='*60}")

        # ── Step 1: Parallel specialist dispatch ─────────────────────
        specialists = {
            "kyc": self.kyc,
            "fraud": self.fraud,
            "credit": self.credit,
            "documents": self.documents,
        }

        specialist_results: dict[str, Any] = {}

        def _dispatch(key: str, agent: BaseAgent) -> tuple[str, dict]:
            out_msg = self.send(agent.name, {"action": f"process_{key}", "applicant": applicant})
            all_messages.append(out_msg.to_dict())
            print(f"  → Dispatched {agent.name}")

            result = agent.run(applicant)

            in_msg = Message(
                sender=agent.name,
                recipient=self.name,
                payload=result,
            )
            self.receive(in_msg)
            all_messages.append(in_msg.to_dict())
            return key, result

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_dispatch, k, a): k for k, a in specialists.items()}
            for future in as_completed(futures):
                key, result = future.result()
                specialist_results[key] = result
                _print_specialist_result(key, result)

        # ── Step 2: Decision Agent ────────────────────────────────────
        dec_out = self.send(self.decision.name, {"action": "decide", "aggregated": specialist_results})
        all_messages.append(dec_out.to_dict())

        decision = self.decision._run(specialist_results)  # noqa: SLF001

        dec_in = Message(
            sender=self.decision.name,
            recipient=self.name,
            payload=decision,
        )
        self.receive(dec_in)
        all_messages.append(dec_in.to_dict())

        # ── Step 3: Assemble artifact ─────────────────────────────────
        elapsed = round(time.time() - started_at, 3)
        artifact = {
            "run_id": run_id,
            "elapsed_seconds": elapsed,
            "decision": decision,
            "specialist_results": specialist_results,
            "messages": all_messages,
        }

        _print_decision(decision, elapsed)
        return artifact


# ─── Pretty-print helpers ──────────────────────────────────────────────────────

def _print_specialist_result(key: str, result: dict) -> None:
    icons = {"kyc": "🔍", "fraud": "🛡️", "credit": "💳", "documents": "📄"}
    icon = icons.get(key, "•")
    if key == "kyc":
        status = "✅" if result["verified"] else "❌"
        print(f"  {icon} KYC        {status}  score={result['score']}")
    elif key == "fraud":
        level = result["risk_level"]
        color = "✅" if level == "low" else ("⚠️" if level == "medium" else "❌")
        print(f"  {icon} Fraud      {color}  risk={result['risk_score']} ({level})")
    elif key == "credit":
        status = "✅" if result["eligible"] else "❌"
        print(f"  {icon} Credit     {status}  score={result['credit_score']} ({result['grade']}), DTI={result['dti_ratio']}")
    elif key == "documents":
        status = "✅" if result["complete"] else f"❌ missing: {result['missing']}"
        print(f"  {icon} Documents  {status}")


def _print_decision(decision: dict, elapsed: float) -> None:
    icons = {
        "APPROVE_FAST_TRACK": "🚀",
        "APPROVE": "✅",
        "HUMAN_REVIEW": "👤",
        "REJECT": "❌",
    }
    icon = icons.get(decision["decision"], "?")
    print(f"\n  {icon}  Decision: {decision['decision']}")
    print(f"     Reasoning: {decision['reasoning']}")
    print(f"     LLM used: {decision.get('llm_used', False)}")
    print(f"     Elapsed:  {elapsed}s")
    print(f"{'='*60}\n")

"""Orchestrator agent - coordinates all other agents."""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..schemas import (
    AgentMessage, LoanApplication, TriageDecision, ToolCall, ToolResponse
)
from ..memory import RunMemory
from ..config import config
from ..messaging import create_message, sign_message
from ..guardrails import redact_pii
from .base import BaseAgent


class Orchestrator(BaseAgent):
    """Orchestrator agent that coordinates the triage process."""

    def __init__(self):
        super().__init__(
            name="orchestrator",
            description="Coordinates all agents and makes final decision"
        )
        self.agents = ["kyc_agent", "fraud_agent", "credit_agent", "documents_agent", "decision_agent"]

    def process(self, input_data: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Orchestrate the triage process."""
        application = LoanApplication(**input_data)
        
        # Create run ID
        run_id = str(uuid.uuid4())
        memory.run_id = run_id
        
        # Initialize messages list
        all_messages = []
        
        # Step 1: Send application to specialist agents
        specialist_results = {}
        for agent_name in self.agents[:-1]:  # All except decision_agent
            result = self._dispatch_to_agent(agent_name, application.model_dump(), memory)
            specialist_results[agent_name] = result
            all_messages.extend(memory.messages[-2:])  # Last 2 messages (request/response)
        
        # Step 2: Send all results to decision agent
        decision_input = {
            "application": application.model_dump(),
            "specialist_results": specialist_results
        }
        decision_result = self._dispatch_to_agent("decision_agent", decision_input, memory)
        
        # Step 3: Create final decision
        final_decision = self._create_decision(decision_result, application)
        
        return {
            "decision": final_decision.model_dump(),
            "messages": [m.model_dump() for m in all_messages],
            "tool_outputs": memory.tool_outputs
        }

    def _dispatch_to_agent(
        self,
        agent_name: str,
        payload: Dict[str, Any],
        memory: RunMemory
    ) -> Dict[str, Any]:
        """Dispatch a message to an agent and record the interaction."""
        # Create request message
        request = create_message(
            sender="orchestrator",
            recipient=agent_name,
            payload=payload
        )
        memory.add_message(request)
        
        # In mock mode, we simulate the agent's response
        # In real implementation, this would call the agent's process method
        response_payload = self._simulate_agent_response(agent_name, payload)
        
        # Create response message
        response = create_message(
            sender=agent_name,
            recipient="orchestrator",
            payload=response_payload
        )
        memory.add_message(response)
        
        return response_payload

    def _simulate_agent_response(
        self,
        agent_name: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate agent response (mock mode)."""
        # This would be replaced with actual agent calls in production
        if agent_name == "kyc_agent":
            return {
                "verified": True,
                "confidence": 0.95,
                "issues": []
            }
        elif agent_name == "fraud_agent":
            return {
                "is_fraud_risk": False,
                "fraud_score": 0.1,
                "red_flags": []
            }
        elif agent_name == "credit_agent":
            return {
                "credit_score": payload.get("credit_score", 720),
                "recommendation": "approve",
                "risk_level": "low"
            }
        elif agent_name == "documents_agent":
            return {
                "documents_verified": True,
                "missing_documents": []
            }
        else:
            return {
                "recommendation": "approve",
                "risk_band": "prime",
                "reasons": ["All checks passed"]
            }

    def _create_decision(
        self,
        decision_result: Dict[str, Any],
        application: LoanApplication
    ) -> TriageDecision:
        """Create final triage decision."""
        return TriageDecision(
            application_id=application.application_id,
            recommendation=decision_result.get("recommendation", "approve"),
            status=self._map_status(decision_result.get("recommendation", "approve")),
            risk_band=decision_result.get("risk_band", "prime"),
            reasons=decision_result.get("reasons", []),
            required_documents=decision_result.get("required_documents", []),
            requires_human_review=decision_result.get("requires_human_review", False),
            estimated_processing_days=3
        )

    def _map_status(self, recommendation: str) -> str:
        """Map recommendation to status."""
        mapping = {
            "approve": "approved",
            "reject": "rejected",
            "human_review": "human_review",
            "approve_fast_track": "approved_fast_track"
        }
        return mapping.get(recommendation, "pending")

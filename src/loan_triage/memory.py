"""Run-scoped memory for artifact accumulation."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .schemas import AgentMessage, ToolCall, ToolResponse


class RunMemory:
    """Memory for a single triage run."""

    def __init__(self, run_id: str, application_id: str):
        self.run_id = run_id
        self.application_id = application_id
        self.messages: List[AgentMessage] = []
        self.tool_outputs: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.total_cost_usd = 0.0
        self.total_tool_calls = 0

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the run history."""
        self.messages.append(message)

    def add_tool_output(self, tool_call: ToolCall, response: ToolResponse) -> None:
        """Record a tool call and its response."""
        self.tool_outputs.append({
            "tool_call_id": tool_call.tool_call_id,
            "tool_name": tool_call.tool_name,
            "parameters": tool_call.parameters,
            "success": response.success,
            "result": response.result,
            "error": response.error,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.total_tool_calls += 1

    def add_cost(self, cost_usd: float) -> None:
        """Add to the total cost."""
        self.total_cost_usd += cost_usd

    def mark_complete(self) -> None:
        """Mark the run as complete."""
        self.end_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "application_id": self.application_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_cost_usd": self.total_cost_usd,
            "total_tool_calls": self.total_tool_calls,
            "messages": [
                {
                    "message_id": m.message_id,
                    "sender": m.sender,
                    "recipient": m.recipient,
                    "payload": m.payload,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.messages
            ],
            "tool_outputs": self.tool_outputs
        }

    def to_json(self) -> str:
        """Convert memory to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

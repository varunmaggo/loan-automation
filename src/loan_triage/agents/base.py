"""Base agent class."""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import llm
from ..schemas import AgentMessage, ToolCall, ToolResponse, TriageDecision
from ..memory import RunMemory
from ..config import config
from ..guardrails import redact_pii, check_prompt_injection


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = llm.get_llm_client()
        self.max_tool_calls = config.MAX_TOOL_CALLS
        self.max_wallclock_seconds = config.MAX_WALLCLOCK_SECONDS

    @abstractmethod
    def process(self, input_data: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Process input and return results."""
        pass

    def execute_with_budget(
        self,
        tool_calls: List[ToolCall],
        memory: RunMemory
    ) -> List[ToolResponse]:
        """Execute tool calls within budget."""
        responses = []
        calls_made = 0
        
        start_time = time.time()
        
        for tool_call in tool_calls:
            # Check budgets
            if calls_made >= self.max_tool_calls:
                break
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_wallclock_seconds:
                break
            
            # Call tool
            response = llm.call_tool(tool_call.tool_name, tool_call.parameters)
            responses.append(response)
            
            # Record in memory
            memory.add_tool_output(tool_call, response)
            calls_made += 1
            
            # Add cost
            memory.add_cost(0.001)  # Mock tool cost
        
        return responses

    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate input data."""
        return llm.config.validate_input(input_data)

    def redact_pii(self, text: str) -> str:
        """Redact PII from text."""
        if config.PII_REDACTION:
            return redact_pii(text)
        return text

    def check_prompt_injection(self, prompt: str) -> bool:
        """Check for prompt injection."""
        return check_prompt_injection(prompt)

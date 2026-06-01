"""LLM client with mock and live modes."""

import json
import time
from typing import Any, Dict, List, Optional

from .config import config
from .schemas import ToolCall, ToolResponse


class MockLLMClient:
    """Mock LLM client for deterministic testing."""

    def __init__(self):
        self.call_count = 0
        self.total_cost = 0.0

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict[str, Any]] = None,
        temperature: float = 0.7
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Generate a deterministic response."""
        self.call_count += 1
        
        # Simple mock logic based on prompt content
        response_text = self._mock_response(system_prompt, user_prompt)
        tool_calls = self._mock_tool_calls(user_prompt)
        
        # Mock cost: $0.0001 per call
        cost = 0.0001
        self.total_cost += cost
        
        return response_text, tool_calls

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate mock response based on prompt."""
        if "fraud" in user_prompt.lower():
            return json.dumps({
                "is_fraud_risk": False,
                "fraud_score": 0.1,
                "red_flags": [],
                "recommendation": "clear"
            })
        elif "credit" in user_prompt.lower():
            return json.dumps({
                "credit_score": 720,
                "credit_history_years": 5,
                "delinquencies": 0,
                "recommendation": "approve"
            })
        elif "kyc" in user_prompt.lower():
            return json.dumps({
                "identity_verified": True,
                "address_verified": True,
                "documents_required": [],
                "recommendation": "clear"
            })
        elif "documents" in user_prompt.lower():
            return json.dumps({
                "documents_uploaded": 3,
                "documents_verified": 3,
                "missing_documents": [],
                "recommendation": "complete"
            })
        else:
            return json.dumps({
                "recommendation": "approve",
                "risk_band": "prime",
                "reasons": ["Good credit score", "Stable employment"],
                "requires_human_review": False
            })

    def _mock_tool_calls(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Generate mock tool calls."""
        tool_calls = []
        if "fraud" in user_prompt.lower():
            tool_calls.append({"tool": "check_fraud_database", "arguments": {}})
        if "credit" in user_prompt.lower():
            tool_calls.append({"tool": "get_credit_report", "arguments": {}})
        if "kyc" in user_prompt.lower():
            tool_calls.append({"tool": "verify_identity", "arguments": {}})
        return tool_calls


class LiveLLMClient:
    """Live LLM client using OpenAI API."""

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.call_count = 0
        self.total_cost = 0.0

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict[str, Any]] = None,
        temperature: float = 0.7
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Generate response using live LLM."""
        self.call_count += 1
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        params = {
            "model": config.MODEL_NAME,
            "messages": messages,
            "temperature": temperature
        }
        
        if tools:
            params["tools"] = tools
        
        response = self.client.chat.completions.create(**params)
        
        # Parse response
        message = response.choices[0].message
        tool_calls = []
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append({
                    "tool": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                })
        
        content = message.content or ""
        
        # Estimate cost (simplified)
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost = (prompt_tokens * 0.00000015 + completion_tokens * 0.0000006)
        self.total_cost += cost
        
        return content, tool_calls


def get_llm_client() -> Any:
    """Get appropriate LLM client based on configuration."""
    if config.LIVE_MODE:
        return LiveLLMClient()
    return MockLLMClient()


def call_tool(tool_name: str, arguments: Dict[str, Any]) -> ToolResponse:
    """Call a tool and return the response."""
    # Mock tool implementations
    mock_tools = {
        "check_fraud_database": lambda: {
            "is_fraud_risk": False,
            "fraud_score": 0.1,
            "red_flags": [],
            "recommendation": "clear"
        },
        "get_credit_report": lambda: {
            "credit_score": 720,
            "credit_history_years": 5,
            "delinquencies": 0,
            "recommendation": "approve"
        },
        "verify_identity": lambda: {
            "identity_verified": True,
            "address_verified": True,
            "documents_required": [],
            "recommendation": "clear"
        },
        "check_documents": lambda: {
            "documents_uploaded": 3,
            "documents_verified": 3,
            "missing_documents": [],
            "recommendation": "complete"
        },
    }
    
    if tool_name in mock_tools:
        result = mock_tools[tool_name]()
        return ToolResponse(
            tool_call_id=f"tool_{time.time()}",
            tool_name=tool_name,
            success=True,
            result=result
        )
    else:
        return ToolResponse(
            tool_call_id=f"tool_{time.time()}",
            tool_name=tool_name,
            success=False,
            error=f"Unknown tool: {tool_name}"
        )

"""
Base agent infrastructure: signed message envelopes, budget enforcement,
and PII redaction for the loan-triage fleet.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


# ─── PII Redaction ────────────────────────────────────────────────────────────

_PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"), "[REDACTED_PHONE]"),
]


def redact_pii(text: str) -> str:
    """Replace known PII patterns with safe placeholders."""
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ─── Signed Message Envelope ──────────────────────────────────────────────────

_HMAC_SECRET = b"fleet-demo-secret-change-in-prod"  # inject via env in real usage


def _sign(payload: str) -> str:
    return hmac.new(_HMAC_SECRET, payload.encode(), hashlib.sha256).hexdigest()


@dataclass
class Message:
    sender: str
    recipient: str
    payload: dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    signature: str = field(init=False)

    def __post_init__(self) -> None:
        self.signature = _sign(json.dumps(self.payload, sort_keys=True))

    def verify(self) -> bool:
        expected = _sign(json.dumps(self.payload, sort_keys=True))
        return hmac.compare_digest(self.signature, expected)

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    def __repr__(self) -> str:
        safe = redact_pii(json.dumps(self.payload))
        return f"Message({self.sender} → {self.recipient}: {safe})"


# ─── Budget Enforcement ───────────────────────────────────────────────────────

class BudgetExceeded(RuntimeError):
    pass


class Budget:
    def __init__(self, max_tool_calls: int, max_wallclock_seconds: float, max_cost_usd: float) -> None:
        self.max_tool_calls = max_tool_calls
        self.max_wallclock_seconds = max_wallclock_seconds
        self.max_cost_usd = max_cost_usd
        self._tool_calls = 0
        self._start = time.monotonic()
        self._cost = 0.0

    def charge(self, cost_usd: float = 0.0) -> None:
        self._tool_calls += 1
        self._cost += cost_usd
        elapsed = time.monotonic() - self._start

        if self._tool_calls > self.max_tool_calls:
            raise BudgetExceeded(f"Tool call limit exceeded ({self._tool_calls}/{self.max_tool_calls})")
        if elapsed > self.max_wallclock_seconds:
            raise BudgetExceeded(f"Time limit exceeded ({elapsed:.1f}s/{self.max_wallclock_seconds}s)")
        if self._cost > self.max_cost_usd:
            raise BudgetExceeded(f"Cost limit exceeded (${self._cost:.4f}/${self.max_cost_usd})")


# ─── Base Agent ───────────────────────────────────────────────────────────────

class BaseAgent:
    """
    All fleet agents inherit from this. Subclasses implement `_run()`.
    Budget is enforced automatically; messages are signed and logged.
    """

    name: str = "base_agent"

    def __init__(
        self,
        max_tool_calls: int = 5,
        max_wallclock_seconds: float = 30.0,
        max_cost_usd: float = 0.25,
    ) -> None:
        self.budget = Budget(max_tool_calls, max_wallclock_seconds, max_cost_usd)
        self.message_log: list[Message] = []

    def send(self, recipient: str, payload: dict) -> Message:
        msg = Message(sender=self.name, recipient=recipient, payload=payload)
        self.message_log.append(msg)
        return msg

    def receive(self, msg: Message) -> None:
        if not msg.verify():
            raise ValueError(f"Message signature verification failed: {msg.message_id}")
        self.message_log.append(msg)

    def run(self, applicant: dict) -> dict:
        """Public entry point. Wraps _run() with budget tracking."""
        self.budget.charge()
        return self._run(applicant)

    def _run(self, applicant: dict) -> dict:
        raise NotImplementedError

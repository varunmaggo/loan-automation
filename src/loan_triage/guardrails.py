"""Guardrails for PII redaction and prompt injection detection."""

import re
from typing import List, Optional


# PII patterns
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
}


def redact_pii(text: str) -> str:
    """Redact PII from text."""
    result = text
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, result)
        for match in matches:
            # Redact with placeholder
            redacted = f"[REDACTED_{pattern_name.upper()}]"
            result = result.replace(match, redacted)
    return result


def check_prompt_injection(prompt: str) -> bool:
    """Check for prompt injection attempts."""
    injection_patterns = [
        r"ignore\s+(previous|all|prior|above|before)",
        r"disregard\s+(previous|all|prior|above|before)",
        r"you\s+are\s+(now|a|an)",
        r"system\s+(override|bypass|ignore)",
        r"ignore\s+instructions?",
    ]
    
    prompt_lower = prompt.lower()
    for pattern in injection_patterns:
        if re.search(pattern, prompt_lower):
            return True
    return False


def validate_input(input_data: dict) -> tuple[bool, Optional[str]]:
    """Validate input data for security issues."""
    # Check for prompt injection in text fields
    for key, value in input_data.items():
        if isinstance(value, str):
            if check_prompt_injection(value):
                return False, f"Potential prompt injection detected in '{key}'"
    
    # Check for excessive length
    for key, value in input_data.items():
        if isinstance(value, str) and len(value) > 10000:
            return False, f"Input '{key}' exceeds maximum length of 10000 characters"
    
    return True, None


def sanitize_output(output: str) -> str:
    """Sanitize output for safe display."""
    # Redact any PII that might have been generated
    return redact_pii(output)

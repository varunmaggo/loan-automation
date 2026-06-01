"""Authentication and authorization utilities."""

import hmac
import hashlib
from typing import Optional

from .config import config


def compute_signature(message: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for a message."""
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def verify_signature(message: str, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected = compute_signature(message, secret)
    return hmac.compare_digest(expected, signature)


def validate_scope(required_scope: str, principal_scopes: list) -> bool:
    """Check if principal has required scope."""
    return required_scope in principal_scopes


def get_principal_scopes(agent_name: str) -> list:
    """Get allowed scopes for an agent."""
    # Define agent scopes
    agent_scopes = {
        "orchestrator": ["read", "write", "control"],
        "kyc_agent": ["read", "kyc_read"],
        "fraud_agent": ["read", "fraud_read"],
        "credit_agent": ["read", "credit_read"],
        "documents_agent": ["read", "documents_read"],
        "decision_agent": ["read", "write", "control"],
    }
    return agent_scopes.get(agent_name, ["read"])

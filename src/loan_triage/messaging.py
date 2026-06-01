"""Agent messaging utilities with HMAC-SHA256 signing."""

import json
import uuid
from datetime import datetime

from .auth import compute_signature, verify_signature
from .config import config
from .schemas import AgentMessage


def create_message(
    sender: str,
    recipient: str,
    payload: dict,
    secret: str = None
) -> AgentMessage:
    """Create a signed agent message."""
    message_id = str(uuid.uuid4())
    payload_json = json.dumps(payload, sort_keys=True)
    
    signature = compute_signature(payload_json, secret or config.AGENT_SHARED_SECRET)
    
    return AgentMessage(
        message_id=message_id,
        sender=sender,
        recipient=recipient,
        payload=payload,
        timestamp=datetime.utcnow(),
        signature=signature
    )


def verify_message(message: AgentMessage, secret: str = None) -> bool:
    """Verify message signature."""
    payload_json = json.dumps(message.payload, sort_keys=True)
    return verify_signature(
        payload_json,
        message.signature,
        secret or config.AGENT_SHARED_SECRET
    )


def sign_message(message: AgentMessage, secret: str = None) -> AgentMessage:
    """Add signature to an unsigned message."""
    payload_json = json.dumps(message.payload, sort_keys=True)
    signature = compute_signature(payload_json, secret or config.AGENT_SHARED_SECRET)
    message.signature = signature
    return message


def format_message_for_logging(message: AgentMessage) -> dict:
    """Format message for logging (excludes signature)."""
    return {
        "message_id": message.message_id,
        "sender": message.sender,
        "recipient": message.recipient,
        "payload": message.payload,
        "timestamp": message.timestamp.isoformat()
    }

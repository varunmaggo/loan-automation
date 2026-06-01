"""Artifact writing utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .config import config


def write_artifact(filename: str, data: Dict[str, Any]) -> Path:
    """Write artifact data to JSON file."""
    artifact_path = config.ARTIFACT_DIR / filename
    
    # Add metadata
    artifact_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "data": data
    }
    
    # Write file
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with open(artifact_path, "w") as f:
        json.dump(artifact_data, f, indent=2)
    
    return artifact_path


def write_run_artifact(run_id: str, run_data: Dict[str, Any]) -> Path:
    """Write a run artifact with standard naming."""
    filename = f"run_{run_id}.json"
    return write_artifact(filename, run_data)


def write_decision_artifact(application_id: str, decision: Dict[str, Any]) -> Path:
    """Write a decision artifact with standard naming."""
    filename = f"decision_{application_id}.json"
    return write_artifact(filename, decision)

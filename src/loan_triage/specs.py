"""YAML spec loader for agents, policy, and evals."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import config


def load_yaml_file(filepath: Path) -> Dict[str, Any]:
    """Load a YAML file and return its contents."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def load_agent_spec(agent_name: str) -> Dict[str, Any]:
    """Load an agent specification."""
    spec_path = config.SPECS_DIR / "agents" / f"{agent_name}.agent.yaml"
    return load_yaml_file(spec_path)


def load_all_agents_specs() -> Dict[str, Dict[str, Any]]:
    """Load all agent specifications."""
    agents_dir = config.SPECS_DIR / "agents"
    agents = {}
    
    for spec_file in agents_dir.glob("*.agent.yaml"):
        agent_name = spec_file.stem
        agents[agent_name] = load_yaml_file(spec_file)
    
    return agents


def load_policy_spec() -> Dict[str, Any]:
    """Load the decision policy specification."""
    spec_path = config.SPECS_DIR / "policy" / "decision_policy.yaml"
    return load_yaml_file(spec_path)


def load_tools_spec() -> Dict[str, Any]:
    """Load the tools specification."""
    spec_path = config.SPECS_DIR / "tools" / "tools.yaml"
    return load_yaml_file(spec_path)


def load_evals_spec() -> Dict[str, Any]:
    """Load the evaluation specification."""
    spec_path = config.SPECS_DIR / "evals" / "triage.eval.yaml"
    return load_yaml_file(spec_path)


def load_system_spec() -> Dict[str, Any]:
    """Load the system specification."""
    spec_path = config.SPECS_DIR / "system.spec.md"
    # For now, return basic structure
    return {
        "name": "loan-triage",
        "version": "0.1.0",
        "description": "Multi-agent loan triage system"
    }

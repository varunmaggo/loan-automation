"""Configuration management via environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # LLM Configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LIVE_MODE: bool = os.getenv("LIVE_MODE", "false").lower() == "true"

    # Runtime limits
    MAX_TOOL_CALLS: int = int(os.getenv("MAX_TOOL_CALLS", "8"))
    MAX_WALLCLOCK_SECONDS: int = int(os.getenv("MAX_WALLCLOCK_SECONDS", "30"))
    MAX_COST_USD: float = float(os.getenv("MAX_COST_USD", "0.25"))

    # Security
    PII_REDACTION: bool = os.getenv("PII_REDACTION", "true").lower() == "true"
    AGENT_SHARED_SECRET: str = os.getenv("AGENT_SHARED_SECRET", "demo-secret")

    # Artifact storage
    ARTIFACT_DIR: Path = Path(os.getenv("ARTIFACT_DIR", "./artifacts"))

    # Evaluation
    DEEPEVAL_TELEMETRY_OPT_OUT: str = os.getenv("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
    RUN_GEVAL: bool = os.getenv("RUN_GEVAL", "false").lower() == "true"

    # Paths
    SPECS_DIR: Path = Path(__file__).parent.parent.parent / "specs"
    EXAMPLES_DIR: Path = Path(__file__).parent.parent.parent / "examples"

    @classmethod
    def validate(cls) -> None:
        """Validate configuration requirements."""
        if cls.LIVE_MODE and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set when LIVE_MODE=true")

        cls.ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()

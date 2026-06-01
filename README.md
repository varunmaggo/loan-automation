# Multi-Agent Loan Triage System

A spec-driven multi-agent system for loan application triage with DeepEval evaluation suite.

## Features

- **Fleet Architecture**: 6 specialized agents (Orchestrator + 4 specialists + Decision)
- **Spec-Driven**: YAML-based specifications for agents, policy, and evaluation
- **DeepEval Integration**: CI/CD gates with 3-tier metrics
- **Observability**: OpenTelemetry spans for tracing
- **Security**: HMAC-SHA256 signed messages, PII redaction, scope validation

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev,evals]"
pip install python-pptx  # for PPTX generator

# Run tests
pytest

# Run evaluations
DEEPEVAL_TELEMETRY_OPT_OUT=YES python -m evals.run_evals

# Generate demo PowerPoint
.venv/bin/python scripts/generate_demo_pptx.py

# Run CLI
loan-triage run examples/app_001.json
```

## Project Structure

```
loan-triage-agent/
├── src/loan_triage/          # Main package
├── specs/                    # YAML specifications
│   ├── agents/              # Agent definitions
│   ├── policy/              # Lending rules
│   ├── tools/               # Tool catalog
│   └── evals/               # Evaluation config
├── evals/                    # DeepEval suite
├── tests/                    # Unit tests
├── diagrams/                 # draw.io diagrams
└── scripts/                  # Utility scripts
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

## License

MIT

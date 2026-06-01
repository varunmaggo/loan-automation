"""Command-line interface for loan triage."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .config import config, Config
from .schemas import LoanApplication, TriageDecision
from .agents.orchestrator import Orchestrator
from .memory import RunMemory
from .artifacts import write_run_artifact, write_decision_artifact

app = typer.Typer(
    name="loan-triage",
    help="Multi-agent loan triage system",
    no_args_is_help=True
)

console = Console()


@app.command()
def run(
    application_path: Path = typer.Argument(
        ...,
        help="Path to loan application JSON file"
    ),
    output_format: str = typer.Option(
        "text",
        help="Output format: text, json, or table"
    )
):
    """Process a loan application through the triage system."""
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Load application
    try:
        with open(application_path) as f:
            application_data = json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Application file not found: {application_path}[/red]")
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in application file: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Validate application schema
    try:
        application = LoanApplication(**application_data)
    except Exception as e:
        console.print(f"[red]Invalid application data: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Process application
    console.print(f"[blue]Processing application {application.application_id}...[/blue]")
    
    memory = RunMemory(
        run_id="run_" + application.application_id,
        application_id=application.application_id
    )
    
    orchestrator = Orchestrator()
    result = orchestrator.process(application.model_dump(), memory)
    
    # Mark run complete
    memory.mark_complete()
    
    # Create decision object
    decision = TriageDecision(**result["decision"])
    
    # Write artifacts
    write_run_artifact(memory.run_id, memory.to_dict())
    write_decision_artifact(application.application_id, decision.model_dump())
    
    # Output results
    if output_format == "json":
        console.print(json.dumps(result, indent=2))
    elif output_format == "table":
        _print_table_output(decision)
    else:
        _print_text_output(decision, memory)
    
    console.print(f"[green]✓ Processing complete[/green]")


@app.command()
def validate_config():
    """Validate configuration."""
    try:
        config.validate()
        console.print("[green]✓ Configuration is valid[/green]")
    except ValueError as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        raise typer.Exit(code=1)


def _print_text_output(decision: TriageDecision, memory: RunMemory):
    """Print results in text format."""
    panel = Panel(
        f"[bold]Application ID:[/bold] {decision.application_id}\n"
        f"[bold]Recommendation:[/bold] {decision.recommendation.upper()}\n"
        f"[bold]Status:[/bold] {decision.status.value}\n"
        f"[bold]Risk Band:[/bold] {decision.risk_band.value}\n"
        f"[bold]Processing Time:[/bold] {memory.end_time - memory.start_time if memory.end_time else 'N/A'}\n"
        f"[bold]Total Cost:[/bold] ${memory.total_cost_usd:.4f}\n"
        f"[bold]Tool Calls:[/bold] {memory.total_tool_calls}\n\n"
        f"[bold]Reasons:[/bold]\n" + "\n".join(f"  • {r}" for r in decision.reasons) if decision.reasons else "  (none)",
        title="Triage Decision",
        border_style="green"
    )
    console.print(panel)


def _print_table_output(decision: TriageDecision):
    """Print results in table format."""
    table = Table(title="Triage Decision")
    
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Application ID", decision.application_id)
    table.add_row("Recommendation", decision.recommendation.upper())
    table.add_row("Status", decision.status.value)
    table.add_row("Risk Band", decision.risk_band.value)
    table.add_row("Requires Human Review", "Yes" if decision.requires_human_review else "No")
    
    if decision.reasons:
        table.add_row("Reasons", "\n".join(decision.reasons))
    
    console.print(table)


if __name__ == "__main__":
    app()

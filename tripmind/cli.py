"""Interactive CLI demo for TripMind V1 ReAct Engine."""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tripmind.config import settings
from tripmind.core.agent import ReActAgent
from tripmind.core.llm import get_llm_provider
from tripmind.tools.registry import default_registry

console = Console()

DEFAULT_QUERY = (
    "I want to visit Kashmir in December for 5 days. I'm going with my wife. "
    "We don't want a hectic trip. We love scenic places and food, but aren't "
    "interested in adventure activities. Budget around ₹80k excluding flights."
)


def run_cli():
    console.print(Panel.fit(
        "[bold cyan]TripMind 🏔️ — Level 1: ReAct Agent Engine[/bold cyan]\n"
        "[dim]Autonomous Adaptive Trip Planning with Multi-Turn Tool Calling[/dim]",
        border_style="cyan"
    ))

    provider_name = settings.TRIPMIND_LLM_PROVIDER
    console.print(f"[bold yellow]Active Provider:[/bold yellow] [green]{provider_name}[/green]")
    console.print(f"[bold yellow]Registered Tools:[/bold yellow] [green]{len(default_registry.list_tools())}[/green]\n")

    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    console.print(Panel(f"[bold white]{query}[/bold white]", title="[bold green]User Goal[/bold green]", border_style="green"))

    # Resolve provider
    try:
        provider = get_llm_provider(provider_name)
    except Exception as e:
        console.print(f"[yellow]Note: Real provider '{provider_name}' initialization notice: {e}[/yellow]")
        console.print("[cyan]Falling back to deterministic Mock Provider for offline demonstration...[/cyan]\n")
        provider = get_llm_provider("mock")

    agent = ReActAgent(provider=provider, registry=default_registry)
    with console.status("[bold green]Agent executing ReAct cycle (Thought -> Action -> Observation)...[/bold green]"):
        plan = agent.plan(query)

    # Display ReAct Execution Trace
    console.print("\n[bold magenta]═══════════════════════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]          🧠 AGENT EXECUTION TRACE (EXPLAINABILITY)         [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════════════════════[/bold magenta]\n")

    for step in plan.execution_trace:
        step_text = Text()
        step_text.append(f"💭 THOUGHT:\n", style="bold yellow")
        step_text.append(f"{step.thought}\n\n", style="italic white")
        step_text.append(f"🛠️  ACTION: {step.tool_name}\n", style="bold cyan")
        step_text.append(f"Args: {step.tool_input}\n\n", style="dim cyan")
        step_text.append(f"👁️  OBSERVATION:\n", style="bold green")
        step_text.append(f"{step.observation[:280]}...\n", style="dim green")

        console.print(Panel(step_text, title=f"[bold]Turn {step.step_number}[/bold]", border_style="magenta"))

    # Display Verified Itinerary
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"[bold cyan]  📋 VERIFIED ITINERARY: {plan.trip_title}  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")

    for day in plan.days:
        day_table = Table(title=f"{day.title} ({day.region})", show_header=True, header_style="bold blue")
        day_table.add_column("Category", style="cyan", width=16)
        day_table.add_column("Details", style="white")

        day_table.add_row("🏨 Stay", f"{day.stay.name} (₹{day.stay.price_per_night_inr:,.0f}/night) [Heated: {'✅' if day.stay.heating_verified else '❌'}]")
        for act in day.activities:
            day_table.add_row("🎯 Activity", f"{act.name} (₹{act.cost_inr:,.0f}) — {act.description}")
        if day.transit:
            day_table.add_row("🚗 Transit", f"{day.transit.origin} ➔ {day.transit.destination} ({day.transit.distance_km} km, ~{day.transit.estimated_duration_hours}h) [Special: {'⚠️ ' + day.transit.advisory if day.transit.requires_special_vehicle else 'Clear'}]")
        day_table.add_row("💰 Daily Total", f"₹{day.daily_cost_inr:,.0f}")
        day_table.add_row("⏱️ Pace", day.pace_notes)
        console.print(day_table)
        console.print()

    # Budget Breakdown Table
    budget_table = Table(title=f"Deterministic Budget Audit (Cap: ₹{plan.budget_summary.budget_cap_inr:,.0f})", show_header=True, header_style="bold green")
    budget_table.add_column("Category", style="cyan")
    budget_table.add_column("Amount (INR)", style="bold white", justify="right")
    budget_table.add_column("Notes", style="dim")

    for item in plan.budget_summary.items:
        budget_table.add_row(item.category, f"₹{item.amount_inr:,.2f}", item.notes)

    budget_table.add_section()
    budget_table.add_row("Subtotal", f"₹{plan.budget_summary.subtotal_inr:,.2f}", "")
    budget_table.add_row("GST (5%)", f"₹{plan.budget_summary.tax_gst_inr:,.2f}", "Composite tourism tax")
    budget_table.add_row("Buffer Cushion", f"₹{plan.budget_summary.buffer_inr:,.2f}", "Winter contingency")
    budget_table.add_section()
    status_color = "green" if plan.budget_summary.is_within_budget else "red"
    budget_table.add_row(
        "[bold]Grand Total[/bold]",
        f"[{status_color}]₹{plan.budget_summary.total_estimated_inr:,.2f}[/{status_color}]",
        f"[{status_color}]{plan.budget_summary.audit_notes}[/{status_color}]"
    )
    console.print(budget_table)

    # Constraints Checklist
    console.print(Panel(
        "\n".join([f"{'✅' if v else '❌'} {k.replace('_', ' ').title()}" for k, v in plan.constraints_verified.items()]),
        title="[bold green]Zero-Math Intuitive Constraint Verification[/bold green]",
        border_style="green",
    ))


if __name__ == "__main__":
    run_cli()

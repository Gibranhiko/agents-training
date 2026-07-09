import time
from datetime import datetime, timezone
from typing import Callable
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from models import Lead, LogEntry, WorkflowState
from observability import configure_logging, get_logger
from routing import route_by_score
from storage import init_db, list_executions, save_execution
from tools import (
    analyze_lead,
    generate_nurture_email,
    generate_recommendation,
    generate_sales_email,
    mark_disqualified,
    research_company,
    score_lead,
)

load_dotenv()
configure_logging()

log = get_logger()
console = Console()


def run_tool(fn: Callable, state: WorkflowState) -> WorkflowState:
    """
    Envuelve cualquier tool con logging y timing automatico.
    Las tools no saben que estan siendo observadas — esa es la idea.
    """
    tool_name = fn.__name__
    start = time.perf_counter()

    log.info("tool.started", tool=tool_name, execution_id=state.execution_id)
    state.execution_log.append(LogEntry(tool=tool_name, event="started"))

    try:
        result = fn(state)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log.info("tool.completed", tool=tool_name, duration_ms=duration_ms, execution_id=state.execution_id)
        result.execution_log.append(LogEntry(tool=tool_name, event="completed", duration_ms=duration_ms))
        result.tool_durations[tool_name] = duration_ms

        return result

    except Exception as e:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.error("tool.failed", tool=tool_name, error=str(e), duration_ms=duration_ms, execution_id=state.execution_id)
        state.execution_log.append(LogEntry(tool=tool_name, event="failed", duration_ms=duration_ms, error=str(e)))
        raise


def run_workflow(lead: Lead) -> WorkflowState:
    state = WorkflowState(lead=lead)
    log.info("workflow.started", execution_id=state.execution_id, company=lead.company_name)

    state = run_tool(research_company, state)
    state = run_tool(analyze_lead, state)
    state = run_tool(score_lead, state)

    route = route_by_score(state)
    state.route_taken = route
    log.info("workflow.routed", route=route, score=state.lead_score.score, execution_id=state.execution_id)

    if route == "high_value":
        state = run_tool(generate_recommendation, state)
        state = run_tool(generate_sales_email, state)
        state.workflow_status = "completed"

    elif route == "nurture":
        state = run_tool(generate_recommendation, state)
        state = run_tool(generate_nurture_email, state)
        state.workflow_status = "completed"

    else:
        state = run_tool(mark_disqualified, state)

    state.completed_at = datetime.now(timezone.utc)
    total_ms = sum(state.tool_durations.values())
    log.info("workflow.completed", execution_id=state.execution_id, status=state.workflow_status, total_ms=round(total_ms, 2))

    save_execution(state)
    return state


def main():
    init_db()

    lead = Lead(
        company_name="Acme Manufacturing",
        website="https://acme.com",
        contact_name="John Doe",
        contact_email="john@acme.com",
    )

    console.print(Panel.fit("[bold green]AI Lead Qualification Workflow[/bold green]", border_style="green"))
    console.print(f"\nLead: [cyan]{lead.company_name}[/cyan]\n")

    state = run_workflow(lead)

    if state.workflow_status == "disqualified":
        console.print(
            Panel(
                f"[bold]Empresa:[/bold] {state.lead.company_name}\n"
                f"[bold]Score:[/bold]   {state.lead_score.score} / 100\n"
                f"[bold]Status:[/bold]  [red]{state.workflow_status}[/red]\n"
                f"[bold]Razon:[/bold]   {state.recommendation.reasoning}",
                title="[bold red]Lead Descalificado[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )
    else:
        console.print(
            Panel(
                f"[bold]Empresa:[/bold]  {state.lead.company_name}\n"
                f"[bold]Contacto:[/bold] {state.lead.contact_name}\n"
                f"[bold]Score:[/bold]    {state.lead_score.score} / 100\n"
                f"[bold]Route:[/bold]    {state.route_taken}\n"
                f"[bold]Accion:[/bold]   {state.recommendation.next_action}\n\n"
                f"[bold]Asunto:[/bold] {state.email_draft.subject}\n\n"
                f"[bold]Email:[/bold]\n{state.email_draft.content}",
                title="[bold green]Resultado Final[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Tiempos por tool
    console.print("\n[bold]Duracion por tool:[/bold]")
    durations_table = Table(show_header=True, header_style="bold")
    durations_table.add_column("Tool")
    durations_table.add_column("ms", justify="right")

    for tool, ms in state.tool_durations.items():
        durations_table.add_row(tool, f"{ms:.0f}")

    durations_table.add_row("-" * 30, "-" * 6)
    durations_table.add_row("[bold]Total[/bold]", f"[bold]{sum(state.tool_durations.values()):.0f}[/bold]")
    console.print(durations_table)

    # Historial
    console.print("\n[bold]Historial de ejecuciones:[/bold]")
    executions = list_executions()
    hist_table = Table(show_header=True, header_style="bold")
    hist_table.add_column("ID", style="dim", width=8)
    hist_table.add_column("Empresa")
    hist_table.add_column("Score", justify="right")
    hist_table.add_column("Route")
    hist_table.add_column("Status")

    for ex in executions:
        hist_table.add_row(
            ex["execution_id"][:8],
            ex["company_name"],
            str(ex["score"]) if ex["score"] else "-",
            ex["route_taken"] or "-",
            ex["status"],
        )

    console.print(hist_table)


if __name__ == "__main__":
    main()

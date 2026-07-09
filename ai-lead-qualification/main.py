from datetime import datetime, timezone
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from models import Lead, WorkflowState
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

console = Console()


def run_workflow(lead: Lead) -> WorkflowState:
    state = WorkflowState(lead=lead)

    state = research_company(state)
    state = analyze_lead(state)
    state = score_lead(state)

    route = route_by_score(state)
    state.route_taken = route
    console.print(f"\n[bold]Routing:[/bold] score={state.lead_score.score} -> [bold magenta]{route}[/bold magenta]")

    if route == "high_value":
        state = generate_recommendation(state)
        state = generate_sales_email(state)
        state.workflow_status = "completed"

    elif route == "nurture":
        state = generate_recommendation(state)
        state = generate_nurture_email(state)
        state.workflow_status = "completed"

    else:
        state = mark_disqualified(state)

    # Registramos cuando termino y persistimos
    state.completed_at = datetime.now(timezone.utc)
    save_execution(state)
    console.print(f"\n[dim]Guardado: execution_id={state.execution_id}[/dim]")

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
    console.print(f"\nLead: [cyan]{lead.company_name}[/cyan]")

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

    # Muestra historial de ejecuciones
    console.print("\n[bold]Historial de ejecuciones:[/bold]")
    executions = list_executions()

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=36)
    table.add_column("Empresa")
    table.add_column("Score")
    table.add_column("Route")
    table.add_column("Status")
    table.add_column("Creado")

    for ex in executions:
        table.add_row(
            ex["execution_id"],
            ex["company_name"],
            str(ex["score"]) if ex["score"] else "-",
            ex["route_taken"] or "-",
            ex["status"],
            ex["created_at"][:19],
        )

    console.print(table)


if __name__ == "__main__":
    main()

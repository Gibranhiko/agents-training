from datetime import datetime, timezone
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.domain.models import Lead
from app.core.observability import configure_logging
from app.storage.repository import init_db, list_executions
from app.workflow.runner import run_workflow

load_dotenv()
configure_logging()

console = Console()


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

    if state.workflow_status == "failed":
        console.print(Panel(
            f"[bold]Fallo en:[/bold] {state.failed_at_tool}\n[bold]Error:[/bold] {state.error}",
            title="[bold red]Workflow Fallido[/bold red]", border_style="red", padding=(1, 2),
        ))
        return

    if state.workflow_status == "disqualified":
        console.print(Panel(
            f"[bold]Score:[/bold] {state.lead_score.score}/100\n[bold]Razon:[/bold] {state.recommendation.reasoning}",
            title="[bold red]Lead Descalificado[/bold red]", border_style="red", padding=(1, 2),
        ))
    else:
        console.print(Panel(
            f"[bold]Empresa:[/bold]  {state.lead.company_name}\n"
            f"[bold]Score:[/bold]    {state.lead_score.score} / 100\n"
            f"[bold]Route:[/bold]    {state.route_taken}\n"
            f"[bold]Accion:[/bold]   {state.recommendation.next_action}\n\n"
            f"[bold]Asunto:[/bold] {state.email_draft.subject}\n\n"
            f"[bold]Email:[/bold]\n{state.email_draft.content}",
            title="[bold green]Resultado Final[/bold green]", border_style="green", padding=(1, 2),
        ))

    console.print("\n[bold]Historial:[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Empresa")
    table.add_column("Score", justify="right")
    table.add_column("Route")
    table.add_column("Status")
    for ex in list_executions():
        table.add_row(ex["execution_id"][:8], ex["company_name"], str(ex["score"] or "-"), ex["route_taken"] or "-", ex["status"])
    console.print(table)


if __name__ == "__main__":
    main()

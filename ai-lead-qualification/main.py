from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from models import Lead, WorkflowState
from tools import (
    analyze_lead,
    determine_next_action,
    generate_email,
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
    state = determine_next_action(state)
    state = generate_email(state)

    return state


def main():
    lead = Lead(
        company_name="Acme Manufacturing",
        website="https://acme.com",
        contact_name="John Doe",
        contact_email="john@acme.com",
    )

    console.print(Panel.fit("[bold green]AI Lead Qualification Workflow[/bold green]", border_style="green"))
    console.print(f"\nLead: [cyan]{lead.company_name}[/cyan]")

    state = run_workflow(lead)

    console.print(
        Panel(
            f"[bold]Empresa:[/bold]  {state.lead.company_name}\n"
            f"[bold]Contacto:[/bold] {state.lead.contact_name}\n"
            f"[bold]Score:[/bold]    {state.lead_score.score} / 100\n"
            f"[bold]Route:[/bold]    {state.recommendation.route}\n"
            f"[bold]Accion:[/bold]   {state.recommendation.next_action}\n\n"
            f"[bold]Asunto:[/bold] {state.email_draft.subject}\n\n"
            f"[bold]Email:[/bold]\n{state.email_draft.content}",
            title="[bold green]Resultado Final[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


if __name__ == "__main__":
    main()

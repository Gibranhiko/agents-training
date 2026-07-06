import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from models import (
    EmailDraft,
    Lead,
    LeadAnalysis,
    LeadScore,
    Recommendation,
    ResearchResult,
    WorkflowState,
)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
console = Console()


def research_company(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 1 — Research Company[/bold blue]")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un investigador de empresas B2B. "
                    "Dado el nombre de una empresa, devuelve un resumen conciso (maximo 100 palabras) "
                    "de su industria, tamano estimado, y posibles necesidades de negocio."
                ),
            },
            {
                "role": "user",
                "content": f"Investiga: {state.lead.company_name} -- {state.lead.website}",
            },
        ],
    )

    state.research = ResearchResult(summary=response.choices[0].message.content)
    console.print(f"[dim]{state.research.summary}[/dim]")
    return state


def analyze_lead(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 2 — Analyze Lead[/bold blue]")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista de ventas B2B. "
                    "Analiza si el lead es buen fit para una solucion de software empresarial. "
                    "Se conciso, maximo 80 palabras."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Lead: {state.lead.model_dump()}\n\n"
                    f"Research: {state.research.summary}\n\n"
                    "Es buen fit? Por que?"
                ),
            },
        ],
    )

    state.analysis = LeadAnalysis(content=response.choices[0].message.content)
    console.print(f"[dim]{state.analysis.content}[/dim]")
    return state


def score_lead(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 3 — Score Lead[/bold blue]")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un sistema de scoring de leads. "
                    "Responde UNICAMENTE con un numero entero del 1 al 100. "
                    "Nada mas. Solo el numero."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Lead: {state.lead.model_dump()}\n\n"
                    f"Research: {state.research.summary}\n\n"
                    f"Analysis: {state.analysis.content}\n\n"
                    "Cual es el score del 1 al 100?"
                ),
            },
        ],
    )

    state.lead_score = LeadScore(score=int(response.choices[0].message.content.strip()))
    console.print(f"Score: [bold yellow]{state.lead_score.score}[/bold yellow] / 100")
    return state


def determine_next_action(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 4 — Determine Next Action[/bold blue]")

    if state.lead_score.score >= 70:
        route = "high_value"
        next_action = "Contacto directo de ventas - prioridad alta"
    else:
        route = "nurture"
        next_action = "Incorporar a campana de nurturing"

    state.recommendation = Recommendation(route=route, next_action=next_action)
    console.print(f"Route: [bold magenta]{state.recommendation.route}[/bold magenta] -> {state.recommendation.next_action}")
    return state


def generate_email(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 5 — Generate Email[/bold blue]")

    if state.recommendation.route == "high_value":
        tone = "directo, enfocado en ROI, con sentido de urgencia"
    else:
        tone = "educativo, de valor, sin presion de venta"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Eres un copywriter de ventas B2B. Escribe en espanol. "
                    f"Tono: {tone}. Maximo 120 palabras. Sin asunto."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Escribe un email de outreach para:\n"
                    f"Nombre: {state.lead.contact_name}\n"
                    f"Empresa: {state.lead.company_name}\n"
                    f"Contexto: {state.research.summary}"
                ),
            },
        ],
    )

    state.email_draft = EmailDraft(content=response.choices[0].message.content)
    console.print("[dim]Email generado.[/dim]")
    return state


def main():
    state = WorkflowState(
        lead=Lead(
            company_name="Acme Manufacturing",
            website="https://acme.com",
            contact_name="John Doe",
            contact_email="john@acme.com",
        )
    )

    console.print(Panel.fit("[bold green]AI Lead Qualification Workflow[/bold green]", border_style="green"))
    console.print(f"\nLead: [cyan]{state.lead.company_name}[/cyan]")

    # Observa como el state evoluciona — imprimimos que campos estan poblados
    def show_state(label: str):
        populated = [f for f, v in state.model_dump().items() if v is not None]
        console.print(f"[dim]  {label}: {populated}[/dim]")

    show_state("antes de research")
    state = research_company(state)

    show_state("antes de analyze")
    state = analyze_lead(state)

    show_state("antes de score")
    state = score_lead(state)

    show_state("antes de routing")
    state = determine_next_action(state)

    show_state("antes de email")
    state = generate_email(state)

    show_state("state final")

    console.print(
        Panel(
            f"[bold]Empresa:[/bold]  {state.lead.company_name}\n"
            f"[bold]Contacto:[/bold] {state.lead.contact_name}\n"
            f"[bold]Score:[/bold]    {state.lead_score.score} / 100\n"
            f"[bold]Route:[/bold]    {state.recommendation.route}\n"
            f"[bold]Accion:[/bold]   {state.recommendation.next_action}\n\n"
            f"[bold]Email:[/bold]\n{state.email_draft.content}",
            title="[bold green]Resultado Final[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


if __name__ == "__main__":
    main()

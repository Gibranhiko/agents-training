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
    console.print("\n[bold blue]Paso 1 -- Research Company[/bold blue]")

    # parse() en lugar de create() -- OpenAI devuelve directamente un ResearchResult
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un investigador de empresas B2B. "
                    "Analiza la empresa y devuelve informacion estructurada sobre ella."
                ),
            },
            {
                "role": "user",
                "content": f"Investiga: {state.lead.company_name} -- {state.lead.website}",
            },
        ],
        response_format=ResearchResult,
    )

    state.research = response.choices[0].message.parsed
    console.print(f"  Industria: [cyan]{state.research.industry}[/cyan]")
    console.print(f"  Tamano: [cyan]{state.research.estimated_size}[/cyan]")
    console.print(f"  Necesidades: [cyan]{state.research.potential_needs}[/cyan]")
    return state


def analyze_lead(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 2 -- Analyze Lead[/bold blue]")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista de ventas B2B. "
                    "Evalua si el lead es buen fit para una solucion de software empresarial."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Lead: {state.lead.model_dump()}\n\n"
                    f"Research: {state.research.model_dump()}\n\n"
                    "Analiza el fit."
                ),
            },
        ],
        response_format=LeadAnalysis,
    )

    state.analysis = response.choices[0].message.parsed
    console.print(f"  Buen fit: [cyan]{state.analysis.is_good_fit}[/cyan]")
    console.print(f"  Fortalezas: [cyan]{state.analysis.strengths}[/cyan]")
    console.print(f"  Preocupaciones: [cyan]{state.analysis.concerns}[/cyan]")
    return state


def score_lead(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 3 -- Score Lead[/bold blue]")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un sistema de scoring de leads B2B. "
                    "Evalua cada criterio del 1 al 10 y calcula un score final del 1 al 100."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Lead: {state.lead.model_dump()}\n\n"
                    f"Research: {state.research.model_dump()}\n\n"
                    f"Analysis: {state.analysis.model_dump()}\n\n"
                    "Genera el score."
                ),
            },
        ],
        response_format=LeadScore,
    )

    state.lead_score = response.choices[0].message.parsed
    console.print(f"  budget_fit:        [yellow]{state.lead_score.budget_fit}[/yellow] / 10")
    console.print(f"  company_size_fit:  [yellow]{state.lead_score.company_size_fit}[/yellow] / 10")
    console.print(f"  industry_fit:      [yellow]{state.lead_score.industry_fit}[/yellow] / 10")
    console.print(f"  urgency:           [yellow]{state.lead_score.urgency}[/yellow] / 10")
    console.print(f"  Score final:       [bold yellow]{state.lead_score.score}[/bold yellow] / 100")
    return state


def determine_next_action(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 4 -- Determine Next Action[/bold blue]")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un estratega de ventas. "
                    "Basandote en el score y el analisis, determina la siguiente accion. "
                    "Usa 'high_value' si score >= 70, 'nurture' si score >= 40, 'disqualify' si score < 40."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Score: {state.lead_score.model_dump()}\n\n"
                    f"Analysis: {state.analysis.model_dump()}\n\n"
                    "Cual es la siguiente accion?"
                ),
            },
        ],
        response_format=Recommendation,
    )

    state.recommendation = response.choices[0].message.parsed
    console.print(f"  Route: [bold magenta]{state.recommendation.route}[/bold magenta]")
    console.print(f"  Accion: [magenta]{state.recommendation.next_action}[/magenta]")
    return state


def generate_email(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 5 -- Generate Email[/bold blue]")

    if state.recommendation.route == "high_value":
        tone = "directo, enfocado en ROI, con sentido de urgencia"
    elif state.recommendation.route == "nurture":
        tone = "educativo, de valor, sin presion de venta"
    else:
        tone = "agradecido pero claro en que no es el momento adecuado"

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Eres un copywriter de ventas B2B. Escribe en espanol. "
                    f"Tono: {tone}. Maximo 120 palabras en el contenido."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Escribe un email de outreach para:\n"
                    f"Nombre: {state.lead.contact_name}\n"
                    f"Empresa: {state.lead.company_name}\n"
                    f"Contexto: {state.research.summary}\n"
                    f"Accion recomendada: {state.recommendation.next_action}"
                ),
            },
        ],
        response_format=EmailDraft,
    )

    state.email_draft = response.choices[0].message.parsed
    console.print(f"  Asunto: [cyan]{state.email_draft.subject}[/cyan]")
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

    state = research_company(state)
    state = analyze_lead(state)
    state = score_lead(state)
    state = determine_next_action(state)
    state = generate_email(state)

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

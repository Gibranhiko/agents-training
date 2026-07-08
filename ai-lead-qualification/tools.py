import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console

from models import (
    EmailDraft,
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


def generate_recommendation(state: WorkflowState) -> WorkflowState:
    """
    El route ya esta decidido en state.route_taken (por routing.py).
    Esta tool solo genera el texto de next_action y reasoning.
    """
    console.print("\n[bold blue]Paso 4 -- Generate Recommendation[/bold blue]")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un estratega de ventas. "
                    f"El route ya fue decidido: '{state.route_taken}'. "
                    "Genera una recomendacion de siguiente accion coherente con ese route."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Score: {state.lead_score.model_dump()}\n\n"
                    f"Analysis: {state.analysis.model_dump()}\n\n"
                    f"Route asignado: {state.route_taken}\n\n"
                    "Genera la recomendacion."
                ),
            },
        ],
        response_format=Recommendation,
    )

    state.recommendation = response.choices[0].message.parsed
    console.print(f"  Accion: [magenta]{state.recommendation.next_action}[/magenta]")
    return state


def generate_sales_email(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 5a -- Generate Sales Email (high_value)[/bold blue]")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un copywriter de ventas B2B. Escribe en espanol. "
                    "Tono: directo, enfocado en ROI, con sentido de urgencia. "
                    "Maximo 120 palabras en el contenido."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Nombre: {state.lead.contact_name}\n"
                    f"Empresa: {state.lead.company_name}\n"
                    f"Contexto: {state.research.summary}\n"
                    f"Accion: {state.recommendation.next_action}"
                ),
            },
        ],
        response_format=EmailDraft,
    )

    state.email_draft = response.choices[0].message.parsed
    console.print(f"  Asunto: [cyan]{state.email_draft.subject}[/cyan]")
    return state


def generate_nurture_email(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 5b -- Generate Nurture Email (nurture)[/bold blue]")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un copywriter de contenido B2B. Escribe en espanol. "
                    "Tono: educativo, de valor, sin presion de venta. "
                    "Maximo 120 palabras en el contenido."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Nombre: {state.lead.contact_name}\n"
                    f"Empresa: {state.lead.company_name}\n"
                    f"Contexto: {state.research.summary}\n"
                    f"Necesidades identificadas: {state.research.potential_needs}"
                ),
            },
        ],
        response_format=EmailDraft,
    )

    state.email_draft = response.choices[0].message.parsed
    console.print(f"  Asunto: [cyan]{state.email_draft.subject}[/cyan]")
    return state


def mark_disqualified(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 5c -- Mark Disqualified[/bold blue]")

    state.recommendation = Recommendation(
        route="disqualify",
        next_action="No continuar con este lead en este momento.",
        reasoning=f"Score de {state.lead_score.score}/100 por debajo del umbral minimo de 40.",
    )
    state.workflow_status = "disqualified"
    console.print(f"  [red]Lead descalificado. Score: {state.lead_score.score}/100[/red]")
    return state

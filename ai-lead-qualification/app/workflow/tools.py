import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console

from app.domain.models import (
    EmailDraft,
    LeadAnalysis,
    LeadScore,
    Recommendation,
    ResearchResult,
    WorkflowState,
)
from app.core.retry import with_retry

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
console = Console()


@with_retry(max_attempts=3, delay_seconds=1.0)
def research_company(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 1 -- Research Company[/bold blue]")
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un investigador de empresas B2B. Analiza la empresa y devuelve informacion estructurada."},
            {"role": "user", "content": f"Investiga: {state.lead.company_name} -- {state.lead.website}"},
        ],
        response_format=ResearchResult,
    )
    state.research = response.choices[0].message.parsed
    console.print(f"  Industria: [cyan]{state.research.industry}[/cyan]")
    console.print(f"  Tamano: [cyan]{state.research.estimated_size}[/cyan]")
    return state


@with_retry(max_attempts=3, delay_seconds=1.0)
def analyze_lead(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 2 -- Analyze Lead[/bold blue]")
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un analista de ventas B2B. Evalua si el lead es buen fit para software empresarial."},
            {"role": "user", "content": f"Lead: {state.lead.model_dump()}\n\nResearch: {state.research.model_dump()}\n\nAnaliza el fit."},
        ],
        response_format=LeadAnalysis,
    )
    state.analysis = response.choices[0].message.parsed
    console.print(f"  Buen fit: [cyan]{state.analysis.is_good_fit}[/cyan]")
    return state


@with_retry(max_attempts=3, delay_seconds=1.0)
def score_lead(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 3 -- Score Lead[/bold blue]")
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un sistema de scoring de leads B2B. Evalua cada criterio del 1 al 10."},
            {"role": "user", "content": f"Lead: {state.lead.model_dump()}\n\nResearch: {state.research.model_dump()}\n\nAnalysis: {state.analysis.model_dump()}\n\nGenera el score."},
        ],
        response_format=LeadScore,
    )
    state.lead_score = response.choices[0].message.parsed
    console.print(f"  Score final: [bold yellow]{state.lead_score.score}[/bold yellow] / 100")
    return state


@with_retry(max_attempts=3, delay_seconds=1.0)
def generate_recommendation(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 4 -- Generate Recommendation[/bold blue]")
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Eres un estratega de ventas. El route ya fue decidido: '{state.route_taken}'. Genera una recomendacion coherente con ese route."},
            {"role": "user", "content": f"Score: {state.lead_score.model_dump()}\n\nAnalysis: {state.analysis.model_dump()}\n\nRoute: {state.route_taken}"},
        ],
        response_format=Recommendation,
    )
    state.recommendation = response.choices[0].message.parsed
    console.print(f"  Accion: [magenta]{state.recommendation.next_action}[/magenta]")
    return state


@with_retry(max_attempts=3, delay_seconds=1.0)
def generate_sales_email(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 5a -- Generate Sales Email[/bold blue]")
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un copywriter B2B. Tono: directo, ROI, urgencia. Maximo 120 palabras."},
            {"role": "user", "content": f"Nombre: {state.lead.contact_name}\nEmpresa: {state.lead.company_name}\nContexto: {state.research.summary}\nAccion: {state.recommendation.next_action}"},
        ],
        response_format=EmailDraft,
    )
    state.email_draft = response.choices[0].message.parsed
    console.print(f"  Asunto: [cyan]{state.email_draft.subject}[/cyan]")
    return state


@with_retry(max_attempts=3, delay_seconds=1.0)
def generate_nurture_email(state: WorkflowState) -> WorkflowState:
    console.print("\n[bold blue]Paso 5b -- Generate Nurture Email[/bold blue]")
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un copywriter B2B. Tono: educativo, sin presion. Maximo 120 palabras."},
            {"role": "user", "content": f"Nombre: {state.lead.contact_name}\nEmpresa: {state.lead.company_name}\nContexto: {state.research.summary}"},
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
        next_action="No continuar con este lead.",
        reasoning=f"Score {state.lead_score.score}/100 por debajo del umbral de 40.",
    )
    state.workflow_status = "disqualified"
    console.print(f"  [red]Lead descalificado. Score: {state.lead_score.score}/100[/red]")
    return state

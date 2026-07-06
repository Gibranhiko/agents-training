from typing import Literal
from pydantic import BaseModel


class Lead(BaseModel):
    company_name: str
    website: str
    contact_name: str
    contact_email: str


class ResearchResult(BaseModel):
    industry: str
    estimated_size: str
    potential_needs: list[str]
    summary: str


class LeadAnalysis(BaseModel):
    is_good_fit: bool
    strengths: list[str]
    concerns: list[str]
    summary: str


class LeadScore(BaseModel):
    # Criterios explícitos — ya no dejamos que el modelo decida el criterio
    budget_fit: int       # 1-10: probabilidad de tener presupuesto
    company_size_fit: int # 1-10: tamano ideal para nuestro producto
    industry_fit: int     # 1-10: industria alineada con nuestra solucion
    urgency: int          # 1-10: necesidad urgente del producto
    score: int            # 1-100: score final ponderado
    reasoning: str        # por que ese score


class Recommendation(BaseModel):
    route: Literal["high_value", "nurture", "disqualify"]
    next_action: str
    reasoning: str


class EmailDraft(BaseModel):
    subject: str
    content: str


class WorkflowState(BaseModel):
    lead: Lead
    research: ResearchResult | None = None
    analysis: LeadAnalysis | None = None
    lead_score: LeadScore | None = None
    recommendation: Recommendation | None = None
    email_draft: EmailDraft | None = None

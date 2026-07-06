from typing import Literal
from pydantic import BaseModel


class Lead(BaseModel):
    company_name: str
    website: str
    contact_name: str
    contact_email: str


class ResearchResult(BaseModel):
    summary: str


class LeadAnalysis(BaseModel):
    content: str


class LeadScore(BaseModel):
    score: int


class Recommendation(BaseModel):
    route: Literal["high_value", "nurture", "disqualify"]
    next_action: str


class EmailDraft(BaseModel):
    content: str


class WorkflowState(BaseModel):
    # El único campo requerido al inicio — el workflow empieza con un lead.
    lead: Lead

    # Estos campos no son "opcionales" en sentido de negocio —
    # todos se van a poblar. Son None solo porque aún no existen al inicio.
    research: ResearchResult | None = None
    analysis: LeadAnalysis | None = None
    lead_score: LeadScore | None = None
    recommendation: Recommendation | None = None
    email_draft: EmailDraft | None = None

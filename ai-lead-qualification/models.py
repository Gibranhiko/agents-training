from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
import uuid


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
    budget_fit: int
    company_size_fit: int
    industry_fit: int
    urgency: int
    score: int
    reasoning: str


class Recommendation(BaseModel):
    route: Literal["high_value", "nurture", "disqualify"]
    next_action: str
    reasoning: str


class EmailDraft(BaseModel):
    subject: str
    content: str


class WorkflowState(BaseModel):
    # Identidad de la ejecucion — se genera al crear el state
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    lead: Lead
    research: ResearchResult | None = None
    analysis: LeadAnalysis | None = None
    lead_score: LeadScore | None = None
    recommendation: Recommendation | None = None
    email_draft: EmailDraft | None = None

    route_taken: str | None = None
    workflow_status: Literal["running", "completed", "disqualified"] = "running"

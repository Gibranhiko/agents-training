from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domain.models import EmailDraft, Lead, WorkflowState
from app.storage.repository import get_execution, list_executions
from app.workflow.runner import run_workflow

router = APIRouter()


class QualifyLeadRequest(BaseModel):
    company_name: str
    website: str
    contact_name: str
    contact_email: str


class ExecutionSummary(BaseModel):
    execution_id: str
    company_name: str
    status: str
    route_taken: str | None
    score: int | None
    created_at: str | None
    completed_at: str | None


@router.post("/leads", response_model=WorkflowState, status_code=201)
def qualify_lead(request: QualifyLeadRequest):
    lead = Lead(
        company_name=request.company_name,
        website=request.website,
        contact_name=request.contact_name,
        contact_email=request.contact_email,
    )
    return run_workflow(lead)


@router.get("/leads", response_model=list[ExecutionSummary])
def get_executions():
    return list_executions()


@router.get("/leads/{execution_id}", response_model=WorkflowState)
def get_lead_execution(execution_id: str):
    state = get_execution(execution_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return state


@router.get("/leads/{execution_id}/email", response_model=EmailDraft)
def get_lead_email(execution_id: str):
    state = get_execution(execution_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    if state.email_draft is None:
        raise HTTPException(status_code=404, detail="No email draft for this execution")
    return state.email_draft

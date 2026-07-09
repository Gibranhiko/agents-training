"""
Testea que los modelos Pydantic validan correctamente y se serializan a JSON.
Sin mocks, sin OpenAI — solo los modelos.
"""
import pytest
from pydantic import ValidationError
from models import Lead, WorkflowState


def test_lead_requires_all_fields():
    with pytest.raises(ValidationError):
        Lead(company_name="Acme")  # faltan campos requeridos


def test_workflow_state_starts_empty(sample_lead):
    state = WorkflowState(lead=sample_lead)

    assert state.research is None
    assert state.analysis is None
    assert state.lead_score is None
    assert state.recommendation is None
    assert state.email_draft is None
    assert state.workflow_status == "running"
    assert state.execution_log == []
    assert state.tool_durations == {}


def test_workflow_state_serializable_at_any_point(sample_lead):
    """
    El state debe poder convertirse a JSON en cualquier momento del workflow,
    aunque la mayoria de sus campos sean None.
    """
    state = WorkflowState(lead=sample_lead)
    json_str = state.model_dump_json()

    assert "execution_id" in json_str
    assert "Acme" in json_str


def test_workflow_state_roundtrip(state_after_score):
    """Serializar y deserializar el state debe producir el mismo objeto."""
    json_str = state_after_score.model_dump_json()
    recovered = WorkflowState.model_validate_json(json_str)

    assert recovered.execution_id == state_after_score.execution_id
    assert recovered.lead_score.score == state_after_score.lead_score.score
    assert recovered.lead.company_name == state_after_score.lead.company_name

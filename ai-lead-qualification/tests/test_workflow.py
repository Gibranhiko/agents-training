"""
Testea el orquestador completo con todas las tools mockeadas.
No verificamos que las tools hagan algo — verificamos que el orquestador
las llame en el orden correcto y maneje bien los estados de falla.
"""
import pytest
import storage
from unittest.mock import patch, MagicMock
from models import EmailDraft, Lead, Recommendation, WorkflowState
from workflow import run_workflow


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_leads.db")
    monkeypatch.setattr(storage, "DB_PATH", db_file)
    storage.init_db()


def make_state_with_score(lead: Lead, score: int) -> WorkflowState:
    """Construye un state completo con score para simular tools previas."""
    from models import ResearchResult, LeadAnalysis, LeadScore
    state = WorkflowState(lead=lead)
    state.research = ResearchResult(
        industry="Manufacturing", estimated_size="500", potential_needs=[], summary="."
    )
    state.analysis = LeadAnalysis(
        is_good_fit=True, strengths=[], concerns=[], summary="."
    )
    state.lead_score = LeadScore(
        budget_fit=8, company_size_fit=7, industry_fit=9, urgency=6,
        score=score, reasoning="."
    )
    return state


def test_high_value_workflow_calls_sales_email(sample_lead):
    high_value_state = make_state_with_score(sample_lead, score=85)
    final_state = make_state_with_score(sample_lead, score=85)
    final_state.recommendation = Recommendation(
        route="high_value", next_action="Schedule demo", reasoning="High score."
    )
    final_state.email_draft = EmailDraft(subject="Hello", content="Sales email.")

    with patch("workflow.research_company", return_value=high_value_state), \
         patch("workflow.analyze_lead", return_value=high_value_state), \
         patch("workflow.score_lead", return_value=high_value_state), \
         patch("workflow.generate_recommendation", return_value=final_state), \
         patch("workflow.generate_sales_email", return_value=final_state) as mock_sales, \
         patch("workflow.generate_nurture_email") as mock_nurture:

        result = run_workflow(sample_lead)

    mock_sales.assert_called_once()
    mock_nurture.assert_not_called()
    assert result.workflow_status == "completed"


def test_nurture_workflow_calls_nurture_email(sample_lead):
    nurture_state = make_state_with_score(sample_lead, score=55)
    final_state = make_state_with_score(sample_lead, score=55)
    final_state.recommendation = Recommendation(
        route="nurture", next_action="Send content", reasoning="Mid score."
    )
    final_state.email_draft = EmailDraft(subject="Resources", content="Nurture email.")

    with patch("workflow.research_company", return_value=nurture_state), \
         patch("workflow.analyze_lead", return_value=nurture_state), \
         patch("workflow.score_lead", return_value=nurture_state), \
         patch("workflow.generate_recommendation", return_value=final_state), \
         patch("workflow.generate_nurture_email", return_value=final_state) as mock_nurture, \
         patch("workflow.generate_sales_email") as mock_sales:

        result = run_workflow(sample_lead)

    mock_nurture.assert_called_once()
    mock_sales.assert_not_called()
    assert result.workflow_status == "completed"


def test_failed_tool_stops_workflow(sample_lead):
    """Si research falla, el workflow se detiene y no llama tools posteriores."""
    with patch("workflow.research_company", side_effect=Exception("API down")) as mock_research, \
         patch("workflow.analyze_lead") as mock_analyze:

        mock_research.__name__ = "research_company"
        result = run_workflow(sample_lead)

    mock_analyze.assert_not_called()
    assert result.workflow_status == "failed"
    assert result.failed_at_tool == "research_company"


def test_failed_state_is_persisted(sample_lead):
    """Un workflow fallido debe quedar guardado en la DB."""
    with patch("workflow.research_company", side_effect=Exception("Network error")):
        result = run_workflow(sample_lead)

    saved = storage.get_execution(result.execution_id)
    assert saved is not None
    assert saved.workflow_status == "failed"

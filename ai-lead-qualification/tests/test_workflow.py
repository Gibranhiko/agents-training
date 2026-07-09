import pytest
import app.storage.repository as repository
from unittest.mock import patch
from app.domain.models import EmailDraft, Lead, LeadAnalysis, LeadScore, Recommendation, ResearchResult, WorkflowState
from app.workflow.runner import run_workflow


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    repository.init_db()


def make_state_with_score(lead: Lead, score: int) -> WorkflowState:
    state = WorkflowState(lead=lead)
    state.research = ResearchResult(industry="Manufacturing", estimated_size="500", potential_needs=[], summary=".")
    state.analysis = LeadAnalysis(is_good_fit=True, strengths=[], concerns=[], summary=".")
    state.lead_score = LeadScore(budget_fit=8, company_size_fit=7, industry_fit=9, urgency=6, score=score, reasoning=".")
    return state


def test_high_value_workflow_calls_sales_email(sample_lead):
    high_value_state = make_state_with_score(sample_lead, score=85)
    final_state = make_state_with_score(sample_lead, score=85)
    final_state.recommendation = Recommendation(route="high_value", next_action="Demo", reasoning="High score.")
    final_state.email_draft = EmailDraft(subject="Hello", content="Sales email.")

    with patch("app.workflow.runner.research_company", return_value=high_value_state), \
         patch("app.workflow.runner.analyze_lead", return_value=high_value_state), \
         patch("app.workflow.runner.score_lead", return_value=high_value_state), \
         patch("app.workflow.runner.generate_recommendation", return_value=final_state), \
         patch("app.workflow.runner.generate_sales_email", return_value=final_state) as mock_sales, \
         patch("app.workflow.runner.generate_nurture_email") as mock_nurture:

        result = run_workflow(sample_lead)

    mock_sales.assert_called_once()
    mock_nurture.assert_not_called()
    assert result.workflow_status == "completed"


def test_nurture_workflow_calls_nurture_email(sample_lead):
    nurture_state = make_state_with_score(sample_lead, score=55)
    final_state = make_state_with_score(sample_lead, score=55)
    final_state.recommendation = Recommendation(route="nurture", next_action="Content", reasoning="Mid score.")
    final_state.email_draft = EmailDraft(subject="Resources", content="Nurture email.")

    with patch("app.workflow.runner.research_company", return_value=nurture_state), \
         patch("app.workflow.runner.analyze_lead", return_value=nurture_state), \
         patch("app.workflow.runner.score_lead", return_value=nurture_state), \
         patch("app.workflow.runner.generate_recommendation", return_value=final_state), \
         patch("app.workflow.runner.generate_nurture_email", return_value=final_state) as mock_nurture, \
         patch("app.workflow.runner.generate_sales_email") as mock_sales:

        result = run_workflow(sample_lead)

    mock_nurture.assert_called_once()
    mock_sales.assert_not_called()
    assert result.workflow_status == "completed"


def test_failed_tool_stops_workflow(sample_lead):
    with patch("app.workflow.runner.research_company", side_effect=Exception("API down")) as mock_research, \
         patch("app.workflow.runner.analyze_lead") as mock_analyze:

        mock_research.__name__ = "research_company"
        result = run_workflow(sample_lead)

    mock_analyze.assert_not_called()
    assert result.workflow_status == "failed"
    assert result.failed_at_tool == "research_company"


def test_failed_state_is_persisted(sample_lead):
    with patch("app.workflow.runner.research_company", side_effect=Exception("Network error")):
        result = run_workflow(sample_lead)

    saved = repository.get_execution(result.execution_id)
    assert saved is not None
    assert saved.workflow_status == "failed"

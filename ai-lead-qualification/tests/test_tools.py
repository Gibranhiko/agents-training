from unittest.mock import MagicMock, patch
import app.workflow.tools as tools
from app.domain.models import LeadScore, ResearchResult


def make_parsed_response(model_instance):
    mock = MagicMock()
    mock.choices[0].message.parsed = model_instance
    return mock


def test_research_company_populates_state(state_after_score):
    state_after_score.research = None
    fake_research = ResearchResult(
        industry="Manufacturing", estimated_size="500 employees",
        potential_needs=["Automation"], summary="Solid manufacturer.",
    )
    with patch.object(tools.client.beta.chat.completions, "parse") as mock_parse:
        mock_parse.return_value = make_parsed_response(fake_research)
        result = tools.research_company(state_after_score)

    assert result.research is not None
    assert result.research.industry == "Manufacturing"


def test_score_lead_populates_score(state_after_score):
    fake_score = LeadScore(
        budget_fit=8, company_size_fit=7, industry_fit=9, urgency=6,
        score=80, reasoning="Great fit.",
    )
    with patch.object(tools.client.beta.chat.completions, "parse") as mock_parse:
        mock_parse.return_value = make_parsed_response(fake_score)
        result = tools.score_lead(state_after_score)

    assert result.lead_score.score == 80


def test_mark_disqualified_sets_status(state_after_score):
    state_after_score.lead_score.score = 20
    result = tools.mark_disqualified(state_after_score)
    assert result.recommendation.route == "disqualify"
    assert result.workflow_status == "disqualified"

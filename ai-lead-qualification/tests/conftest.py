import pytest
from models import Lead, LeadScore, ResearchResult, LeadAnalysis, WorkflowState


@pytest.fixture
def sample_lead() -> Lead:
    return Lead(
        company_name="Acme Manufacturing",
        website="https://acme.com",
        contact_name="John Doe",
        contact_email="john@acme.com",
    )


@pytest.fixture
def state_after_score(sample_lead) -> WorkflowState:
    """State con score poblado — listo para testear routing."""
    state = WorkflowState(lead=sample_lead)
    state.research = ResearchResult(
        industry="Manufacturing",
        estimated_size="500 employees",
        potential_needs=["Supply chain", "Automation"],
        summary="Mid-sized manufacturer.",
    )
    state.analysis = LeadAnalysis(
        is_good_fit=True,
        strengths=["Good budget", "Clear need"],
        concerns=["Long sales cycle"],
        summary="Strong fit overall.",
    )
    state.lead_score = LeadScore(
        budget_fit=8,
        company_size_fit=7,
        industry_fit=9,
        urgency=6,
        score=75,
        reasoning="Strong industry fit.",
    )
    return state

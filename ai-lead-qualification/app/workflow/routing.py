from app.domain.models import WorkflowState


def route_by_score(state: WorkflowState) -> str:
    score = state.lead_score.score
    if score >= 70:
        return "high_value"
    elif score >= 40:
        return "nurture"
    else:
        return "disqualify"

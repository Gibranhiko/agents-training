from models import WorkflowState


def route_by_score(state: WorkflowState) -> str:
    """
    Logica determinista — el route lo decides TU, no el LLM.
    El LLM genera texto; el routing decide el flujo.
    """
    score = state.lead_score.score

    if score >= 70:
        return "high_value"
    elif score >= 40:
        return "nurture"
    else:
        return "disqualify"

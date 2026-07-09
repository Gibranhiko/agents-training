import pytest
from app.workflow.routing import route_by_score


def test_high_value_at_boundary(state_after_score):
    state_after_score.lead_score.score = 70
    assert route_by_score(state_after_score) == "high_value"


def test_high_value_above_boundary(state_after_score):
    state_after_score.lead_score.score = 95
    assert route_by_score(state_after_score) == "high_value"


def test_nurture_at_boundary(state_after_score):
    state_after_score.lead_score.score = 40
    assert route_by_score(state_after_score) == "nurture"


def test_nurture_just_below_high_value(state_after_score):
    state_after_score.lead_score.score = 69
    assert route_by_score(state_after_score) == "nurture"


def test_disqualify_at_boundary(state_after_score):
    state_after_score.lead_score.score = 39
    assert route_by_score(state_after_score) == "disqualify"


def test_disqualify_at_zero(state_after_score):
    state_after_score.lead_score.score = 1
    assert route_by_score(state_after_score) == "disqualify"

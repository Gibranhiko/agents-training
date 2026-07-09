from datetime import datetime, timezone
from typing import Callable

from models import Lead, LogEntry, WorkflowState
from observability import get_logger
from routing import route_by_score
from storage import save_execution
from tools import (
    analyze_lead,
    generate_nurture_email,
    generate_recommendation,
    generate_sales_email,
    mark_disqualified,
    research_company,
    score_lead,
)

import time

log = get_logger()


def run_tool(fn: Callable, state: WorkflowState) -> WorkflowState:
    tool_name = getattr(fn, '__name__', str(fn))
    start = time.perf_counter()

    log.info("tool.started", tool=tool_name, execution_id=state.execution_id)
    state.execution_log.append(LogEntry(tool=tool_name, event="started"))

    try:
        result = fn(state)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log.info("tool.completed", tool=tool_name, duration_ms=duration_ms, execution_id=state.execution_id)
        result.execution_log.append(LogEntry(tool=tool_name, event="completed", duration_ms=duration_ms))
        result.tool_durations[tool_name] = duration_ms
        return result

    except Exception as e:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.error("tool.failed", tool=tool_name, error=str(e), duration_ms=duration_ms, execution_id=state.execution_id)

        state.execution_log.append(LogEntry(tool=tool_name, event="failed", duration_ms=duration_ms, error=str(e)))
        state.workflow_status = "failed"
        state.failed_at_tool = tool_name
        state.error = str(e)
        state.completed_at = datetime.now(timezone.utc)

        save_execution(state)
        return state


def run_workflow(lead: Lead) -> WorkflowState:
    state = WorkflowState(lead=lead)
    log.info("workflow.started", execution_id=state.execution_id, company=lead.company_name)

    state = run_tool(research_company, state)
    if state.workflow_status == "failed":
        return state

    state = run_tool(analyze_lead, state)
    if state.workflow_status == "failed":
        return state

    state = run_tool(score_lead, state)
    if state.workflow_status == "failed":
        return state

    route = route_by_score(state)
    state.route_taken = route
    log.info("workflow.routed", route=route, score=state.lead_score.score, execution_id=state.execution_id)

    if route == "high_value":
        state = run_tool(generate_recommendation, state)
        if state.workflow_status != "failed":
            state = run_tool(generate_sales_email, state)

    elif route == "nurture":
        state = run_tool(generate_recommendation, state)
        if state.workflow_status != "failed":
            state = run_tool(generate_nurture_email, state)

    else:
        state = run_tool(mark_disqualified, state)

    if state.workflow_status == "running":
        state.workflow_status = "completed"

    state.completed_at = datetime.now(timezone.utc)
    total_ms = sum(state.tool_durations.values())
    log.info("workflow.completed", execution_id=state.execution_id, status=state.workflow_status, total_ms=round(total_ms, 2))

    save_execution(state)
    return state

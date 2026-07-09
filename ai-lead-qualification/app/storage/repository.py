from app.storage.database import get_engine, get_session
from app.storage.orm_models import Base, WorkflowExecutionORM
from app.domain.models import WorkflowState


def init_db() -> None:
    """Crea las tablas si no existen."""
    Base.metadata.create_all(get_engine())


def save_execution(state: WorkflowState) -> None:
    with get_session() as session:
        existing = session.get(WorkflowExecutionORM, state.execution_id)

        if existing:
            existing.status       = state.workflow_status
            existing.route_taken  = state.route_taken
            existing.score        = state.lead_score.score if state.lead_score else None
            existing.state_json   = state.model_dump_json()
            existing.completed_at = state.completed_at
        else:
            session.add(WorkflowExecutionORM(
                id           = state.execution_id,
                company_name = state.lead.company_name,
                status       = state.workflow_status,
                route_taken  = state.route_taken,
                score        = state.lead_score.score if state.lead_score else None,
                state_json   = state.model_dump_json(),
                created_at   = state.created_at,
                completed_at = state.completed_at,
            ))


def get_execution(execution_id: str) -> WorkflowState | None:
    with get_session() as session:
        obj = session.get(WorkflowExecutionORM, execution_id)
        if obj is None:
            return None
        return WorkflowState.model_validate_json(obj.state_json)


def list_executions() -> list[dict]:
    with get_session() as session:
        rows = (
            session.query(WorkflowExecutionORM)
            .order_by(WorkflowExecutionORM.created_at.desc())
            .all()
        )
        return [
            {
                "execution_id": row.id,
                "company_name": row.company_name,
                "status":       row.status,
                "route_taken":  row.route_taken,
                "score":        row.score,
                "created_at":   row.created_at.isoformat() if row.created_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            }
            for row in rows
        ]

import sqlite3
import json
from datetime import datetime
from models import WorkflowState

DB_PATH = "leads.db"


def init_db() -> None:
    """Crea la tabla si no existe. Se llama al arrancar la app."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id           TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                status       TEXT NOT NULL,
                route_taken  TEXT,
                score        INTEGER,
                state_json   TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        conn.commit()


def save_execution(state: WorkflowState) -> None:
    """Guarda o actualiza una ejecucion. Llama esto al final del workflow."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO workflow_executions
                (id, company_name, status, route_taken, score, state_json, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status       = excluded.status,
                route_taken  = excluded.route_taken,
                score        = excluded.score,
                state_json   = excluded.state_json,
                completed_at = excluded.completed_at
        """, (
            state.execution_id,
            state.lead.company_name,
            state.workflow_status,
            state.route_taken,
            state.lead_score.score if state.lead_score else None,
            state.model_dump_json(),
            state.created_at.isoformat(),
            state.completed_at.isoformat() if state.completed_at else None,
        ))
        conn.commit()


def get_execution(execution_id: str) -> WorkflowState | None:
    """Recupera una ejecucion por su ID."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT state_json FROM workflow_executions WHERE id = ?",
            (execution_id,)
        ).fetchone()

    if row is None:
        return None

    return WorkflowState.model_validate_json(row[0])


def list_executions() -> list[dict]:
    """Lista todas las ejecuciones — sin el state_json completo para no saturar."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT id, company_name, status, route_taken, score, created_at, completed_at
            FROM workflow_executions
            ORDER BY created_at DESC
        """).fetchall()

    return [
        {
            "execution_id": row[0],
            "company_name": row[1],
            "status":       row[2],
            "route_taken":  row[3],
            "score":        row[4],
            "created_at":   row[5],
            "completed_at": row[6],
        }
        for row in rows
    ]

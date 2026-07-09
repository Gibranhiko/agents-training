"""
Testea la capa de persistencia con una base de datos temporal.
Cada test arranca con una DB limpia — sin contaminar leads.db.
"""
import pytest
import storage
from models import WorkflowState


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Redirige DB_PATH a un archivo temporal para cada test."""
    db_file = str(tmp_path / "test_leads.db")
    monkeypatch.setattr(storage, "DB_PATH", db_file)
    storage.init_db()


def test_save_and_retrieve(state_after_score):
    state_after_score.workflow_status = "completed"
    storage.save_execution(state_after_score)

    recovered = storage.get_execution(state_after_score.execution_id)

    assert recovered is not None
    assert recovered.execution_id == state_after_score.execution_id
    assert recovered.lead_score.score == state_after_score.lead_score.score
    assert recovered.workflow_status == "completed"


def test_get_nonexistent_returns_none():
    result = storage.get_execution("id-que-no-existe")
    assert result is None


def test_list_executions_empty():
    assert storage.list_executions() == []


def test_list_executions_shows_saved(state_after_score):
    state_after_score.workflow_status = "completed"
    state_after_score.route_taken = "high_value"
    storage.save_execution(state_after_score)

    executions = storage.list_executions()

    assert len(executions) == 1
    assert executions[0]["execution_id"] == state_after_score.execution_id
    assert executions[0]["status"] == "completed"
    assert executions[0]["route_taken"] == "high_value"


def test_save_updates_existing(state_after_score):
    """Guardar dos veces el mismo execution_id actualiza, no duplica."""
    storage.save_execution(state_after_score)

    state_after_score.workflow_status = "completed"
    storage.save_execution(state_after_score)

    assert len(storage.list_executions()) == 1
    assert storage.list_executions()[0]["status"] == "completed"

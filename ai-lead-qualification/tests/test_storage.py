import pytest
import app.storage.repository as repository


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    repository.init_db()


def test_save_and_retrieve(state_after_score):
    state_after_score.workflow_status = "completed"
    repository.save_execution(state_after_score)

    recovered = repository.get_execution(state_after_score.execution_id)
    assert recovered is not None
    assert recovered.execution_id == state_after_score.execution_id
    assert recovered.lead_score.score == state_after_score.lead_score.score
    assert recovered.workflow_status == "completed"


def test_get_nonexistent_returns_none():
    assert repository.get_execution("id-que-no-existe") is None


def test_list_executions_empty():
    assert repository.list_executions() == []


def test_list_executions_shows_saved(state_after_score):
    state_after_score.workflow_status = "completed"
    state_after_score.route_taken = "high_value"
    repository.save_execution(state_after_score)

    executions = repository.list_executions()
    assert len(executions) == 1
    assert executions[0]["execution_id"] == state_after_score.execution_id
    assert executions[0]["status"] == "completed"
    assert executions[0]["route_taken"] == "high_value"


def test_save_updates_existing(state_after_score):
    repository.save_execution(state_after_score)
    state_after_score.workflow_status = "completed"
    repository.save_execution(state_after_score)

    assert len(repository.list_executions()) == 1
    assert repository.list_executions()[0]["status"] == "completed"

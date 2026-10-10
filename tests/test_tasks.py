import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_task(client, title="Task", description=None):
    r = client.post("/tasks/", json={"title": title, "description": description})
    assert r.status_code == 201
    return r.json()


def set_status(client, task_id, status):
    return client.put(f"/tasks/{task_id}", json={"status": status})


# ---------- CRUD ----------
def test_create_task_defaults_to_pending(client):
    t = make_task(client, "Write report", "details")
    assert t["id"] == 1
    assert t["status"] == "pending"
    assert t["description"] == "details"
    assert t["created_at"] is not None


def test_create_requires_title(client):
    assert client.post("/tasks/", json={}).status_code == 422


def test_create_rejects_blank_title(client):
    assert client.post("/tasks/", json={"title": "   "}).status_code == 422


def test_list_tasks(client):
    assert client.get("/tasks/").json() == []
    make_task(client, "A")
    make_task(client, "B")
    assert [t["title"] for t in client.get("/tasks/").json()] == ["A", "B"]


def test_get_task(client):
    t = make_task(client)
    r = client.get(f"/tasks/{t['id']}")
    assert r.status_code == 200 and r.json()["id"] == t["id"]


def test_get_missing_task_404(client):
    assert client.get("/tasks/999").status_code == 404


def test_update_title_and_description(client):
    t = make_task(client, "Old")
    r = client.put(f"/tasks/{t['id']}", json={"title": "New", "description": "d"})
    assert r.status_code == 200
    assert r.json()["title"] == "New" and r.json()["description"] == "d"
    assert r.json()["status"] == "pending"


def test_update_missing_task_404(client):
    assert set_status(client, 999, "in-progress").status_code == 404


def test_update_null_title_rejected(client):
    t = make_task(client)
    assert client.put(f"/tasks/{t['id']}", json={"title": None}).status_code == 422


def test_delete_task(client):
    t = make_task(client)
    assert client.delete(f"/tasks/{t['id']}").status_code == 204
    assert client.get(f"/tasks/{t['id']}").status_code == 404


def test_delete_missing_task_404(client):
    assert client.delete("/tasks/999").status_code == 404


# ---------- Status transition rules ----------
def test_full_valid_flow(client):
    t = make_task(client)
    r = set_status(client, t["id"], "in-progress")
    assert r.status_code == 200 and r.json()["status"] == "in-progress"
    r = set_status(client, t["id"], "completed")
    assert r.status_code == 200 and r.json()["status"] == "completed"


def test_skip_pending_to_completed_rejected(client):
    t = make_task(client)
    r = set_status(client, t["id"], "completed")
    assert r.status_code == 400
    assert "skip" in r.json()["detail"].lower()
    assert client.get(f"/tasks/{t['id']}").json()["status"] == "pending"


def test_downgrade_completed_to_in_progress_rejected(client):
    t = make_task(client)
    set_status(client, t["id"], "in-progress")
    set_status(client, t["id"], "completed")
    r = set_status(client, t["id"], "in-progress")
    assert r.status_code == 400
    assert "downgrade" in r.json()["detail"].lower()


def test_downgrade_completed_to_pending_rejected(client):
    t = make_task(client)
    set_status(client, t["id"], "in-progress")
    set_status(client, t["id"], "completed")
    assert set_status(client, t["id"], "pending").status_code == 400


def test_downgrade_in_progress_to_pending_rejected(client):
    t = make_task(client)
    set_status(client, t["id"], "in-progress")
    assert set_status(client, t["id"], "pending").status_code == 400


def test_same_status_is_noop(client):
    t = make_task(client)
    assert set_status(client, t["id"], "pending").status_code == 200


def test_invalid_status_value_422(client):
    t = make_task(client)
    assert set_status(client, t["id"], "done").status_code == 422


def test_invalid_transition_does_not_apply_other_changes(client):
    t = make_task(client, "Keep")
    r = client.put(f"/tasks/{t['id']}", json={"title": "Changed", "status": "completed"})
    assert r.status_code == 400
    assert client.get(f"/tasks/{t['id']}").json()["title"] == "Keep"


def test_swagger_and_openapi_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200

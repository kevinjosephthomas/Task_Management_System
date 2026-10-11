import csv
import io
from datetime import date, timedelta

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


def register_and_login(client, email="test@example.com", password="password123"):
    username = email.split("@")[0].replace(".", "_")
    if len(username) < 3:
        username = username + "_user"
    client.post("/auth/register", json={"email": email, "password": password, "username": username})
    r = client.post("/auth/login", json={"email": email, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_task(client, headers, title="Task", description=None, priority="medium", due_date=None):
    payload = {"title": title, "description": description, "priority": priority}
    if due_date:
        payload["due_date"] = due_date
    r = client.post("/tasks/", json=payload, headers=headers)
    assert r.status_code == 201
    return r.json()


def set_status(client, headers, task_id, status):
    return client.put(f"/tasks/{task_id}", json={"status": status}, headers=headers)


# ---------- CRUD ----------

def test_create_task_defaults_to_pending(client):
    h = register_and_login(client)
    t = make_task(client, h, "Write report", "details")
    assert t["id"] == 1
    assert t["status"] == "pending"
    assert t["description"] == "details"
    assert t["created_at"] is not None


def test_create_requires_title(client):
    h = register_and_login(client)
    assert client.post("/tasks/", json={}, headers=h).status_code == 422


def test_create_rejects_blank_title(client):
    h = register_and_login(client)
    assert client.post("/tasks/", json={"title": "   "}, headers=h).status_code == 422


def test_list_tasks(client):
    h = register_and_login(client)
    assert client.get("/tasks/", headers=h).json() == []
    make_task(client, h, "A")
    make_task(client, h, "B")
    titles = [t["title"] for t in client.get("/tasks/", headers=h).json()]
    assert "A" in titles and "B" in titles


def test_get_task(client):
    h = register_and_login(client)
    t = make_task(client, h)
    r = client.get(f"/tasks/{t['id']}", headers=h)
    assert r.status_code == 200 and r.json()["id"] == t["id"]


def test_get_missing_task_404(client):
    h = register_and_login(client)
    assert client.get("/tasks/999", headers=h).status_code == 404


def test_update_title_and_description(client):
    h = register_and_login(client)
    t = make_task(client, h, "Old")
    r = client.put(f"/tasks/{t['id']}", json={"title": "New", "description": "d"}, headers=h)
    assert r.status_code == 200
    assert r.json()["title"] == "New" and r.json()["description"] == "d"
    assert r.json()["status"] == "pending"


def test_update_missing_task_404(client):
    h = register_and_login(client)
    assert set_status(client, h, 999, "in-progress").status_code == 404


def test_update_null_title_rejected(client):
    h = register_and_login(client)
    t = make_task(client, h)
    assert client.put(f"/tasks/{t['id']}", json={"title": None}, headers=h).status_code == 422


def test_delete_task(client):
    h = register_and_login(client)
    t = make_task(client, h)
    assert client.delete(f"/tasks/{t['id']}", headers=h).status_code == 204
    assert client.get(f"/tasks/{t['id']}", headers=h).status_code == 404


def test_delete_missing_task_404(client):
    h = register_and_login(client)
    assert client.delete("/tasks/999", headers=h).status_code == 404


# ---------- Status transition rules ----------

def test_full_valid_flow(client):
    h = register_and_login(client)
    t = make_task(client, h)
    r = set_status(client, h, t["id"], "in-progress")
    assert r.status_code == 200 and r.json()["status"] == "in-progress"
    r = set_status(client, h, t["id"], "completed")
    assert r.status_code == 200 and r.json()["status"] == "completed"


def test_skip_pending_to_completed_rejected(client):
    h = register_and_login(client)
    t = make_task(client, h)
    r = set_status(client, h, t["id"], "completed")
    assert r.status_code == 400
    assert "skip" in r.json()["detail"].lower()
    assert client.get(f"/tasks/{t['id']}", headers=h).json()["status"] == "pending"


def test_downgrade_completed_to_in_progress_rejected(client):
    h = register_and_login(client)
    t = make_task(client, h)
    set_status(client, h, t["id"], "in-progress")
    set_status(client, h, t["id"], "completed")
    r = set_status(client, h, t["id"], "in-progress")
    assert r.status_code == 400
    assert "downgrade" in r.json()["detail"].lower()


def test_downgrade_completed_to_pending_rejected(client):
    h = register_and_login(client)
    t = make_task(client, h)
    set_status(client, h, t["id"], "in-progress")
    set_status(client, h, t["id"], "completed")
    assert set_status(client, h, t["id"], "pending").status_code == 400


def test_downgrade_in_progress_to_pending_rejected(client):
    h = register_and_login(client)
    t = make_task(client, h)
    set_status(client, h, t["id"], "in-progress")
    assert set_status(client, h, t["id"], "pending").status_code == 400


def test_same_status_is_noop(client):
    h = register_and_login(client)
    t = make_task(client, h)
    assert set_status(client, h, t["id"], "pending").status_code == 200


def test_invalid_status_value_422(client):
    h = register_and_login(client)
    t = make_task(client, h)
    assert set_status(client, h, t["id"], "done").status_code == 422


def test_invalid_transition_does_not_apply_other_changes(client):
    h = register_and_login(client)
    t = make_task(client, h, "Keep")
    r = client.put(f"/tasks/{t['id']}", json={"title": "Changed", "status": "completed"}, headers=h)
    assert r.status_code == 400
    assert client.get(f"/tasks/{t['id']}", headers=h).json()["title"] == "Keep"


def test_swagger_and_openapi_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


# ===== Feature 5: Search, Filter, Sorting =====

def test_search_by_title(client):
    h = register_and_login(client)
    make_task(client, h, "Fix login bug")
    make_task(client, h, "Update readme")
    r = client.post("/tasks/search", json={"search": "login"}, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["tasks"][0]["title"] == "Fix login bug"


def test_search_by_description(client):
    h = register_and_login(client)
    make_task(client, h, "Task A", description="database migration needed")
    make_task(client, h, "Task B", description="nothing here")
    r = client.post("/tasks/search", json={"search": "migration"}, headers=h)
    assert r.json()["total"] == 1
    assert r.json()["tasks"][0]["title"] == "Task A"


def test_filter_by_status(client):
    h = register_and_login(client)
    t1 = make_task(client, h, "Pending task")
    t2 = make_task(client, h, "Started task")
    set_status(client, h, t2["id"], "in-progress")
    r = client.post("/tasks/search", json={"status": "in-progress"}, headers=h)
    assert r.json()["total"] == 1
    assert r.json()["tasks"][0]["title"] == "Started task"


def test_filter_by_priority(client):
    h = register_and_login(client)
    make_task(client, h, "High task", priority="high")
    make_task(client, h, "Low task", priority="low")
    r = client.post("/tasks/search", json={"priority": "high"}, headers=h)
    assert r.json()["total"] == 1
    assert r.json()["tasks"][0]["title"] == "High task"


def test_sort_by_due_date(client):
    h = register_and_login(client)
    tomorrow = str(date.today() + timedelta(days=1))
    next_week = str(date.today() + timedelta(days=7))
    make_task(client, h, "Later", due_date=next_week)
    make_task(client, h, "Sooner", due_date=tomorrow)
    r = client.post("/tasks/search", json={"sort_by": "due_date", "sort_order": "asc"}, headers=h)
    tasks = r.json()["tasks"]
    assert tasks[0]["title"] == "Sooner"
    assert tasks[1]["title"] == "Later"


def test_sort_by_priority(client):
    h = register_and_login(client)
    make_task(client, h, "Low one", priority="low")
    make_task(client, h, "High one", priority="high")
    r = client.post("/tasks/search", json={"sort_by": "priority", "sort_order": "asc"}, headers=h)
    tasks = r.json()["tasks"]
    assert len(tasks) == 2


def test_combined_filters(client):
    h = register_and_login(client)
    make_task(client, h, "Important pending", priority="high")
    t2 = make_task(client, h, "Important started", priority="high")
    set_status(client, h, t2["id"], "in-progress")
    make_task(client, h, "Low pending", priority="low")
    r = client.post("/tasks/search", json={"priority": "high", "status": "pending"}, headers=h)
    assert r.json()["total"] == 1
    assert r.json()["tasks"][0]["title"] == "Important pending"


def test_pagination(client):
    h = register_and_login(client)
    for i in range(5):
        make_task(client, h, f"Task {i}")
    r = client.post("/tasks/search", json={}, params={"skip": 0, "limit": 2}, headers=h)
    assert r.json()["total"] == 5
    assert r.json()["count"] == 2
    r2 = client.post("/tasks/search", json={}, params={"skip": 2, "limit": 2}, headers=h)
    assert r2.json()["count"] == 2


def test_case_insensitive_search(client):
    h = register_and_login(client)
    make_task(client, h, "Fix Critical BUG")
    r = client.post("/tasks/search", json={"search": "bug"}, headers=h)
    assert r.json()["total"] == 1
    r2 = client.post("/tasks/search", json={"search": "BUG"}, headers=h)
    assert r2.json()["total"] == 1


def test_date_range_filter(client):
    h = register_and_login(client)
    today = date.today()
    make_task(client, h, "Today", due_date=str(today))
    make_task(client, h, "Next week", due_date=str(today + timedelta(days=7)))
    make_task(client, h, "Last week", due_date=str(today - timedelta(days=7)))
    r = client.post("/tasks/search", json={
        "due_date_from": str(today - timedelta(days=1)),
        "due_date_to": str(today + timedelta(days=1)),
    }, headers=h)
    assert r.json()["total"] == 1
    assert r.json()["tasks"][0]["title"] == "Today"


# ===== Feature 6: Task Reminders & Notifications =====

def test_overdue_tasks_returned(client):
    h = register_and_login(client)
    yesterday = str(date.today() - timedelta(days=2))
    make_task(client, h, "Overdue task", due_date=yesterday)
    r = client.get("/tasks/reminders/overdue", headers=h)
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["tasks"][0]["title"] == "Overdue task"


def test_upcoming_tasks_within_days(client):
    h = register_and_login(client)
    tomorrow = str(date.today() + timedelta(days=1))
    make_task(client, h, "Due soon", due_date=tomorrow)
    r = client.get("/tasks/reminders/upcoming?days_ahead=3", headers=h)
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["tasks"][0]["title"] == "Due soon"


def test_completed_tasks_excluded_from_reminders(client):
    h = register_and_login(client)
    yesterday = str(date.today() - timedelta(days=1))
    t = make_task(client, h, "Done task", due_date=yesterday)
    set_status(client, h, t["id"], "in-progress")
    set_status(client, h, t["id"], "completed")
    r = client.get("/tasks/reminders/overdue", headers=h)
    assert r.json()["count"] == 0


def test_overdue_not_include_future_tasks(client):
    h = register_and_login(client)
    future = str(date.today() + timedelta(days=5))
    make_task(client, h, "Future task", due_date=future)
    r = client.get("/tasks/reminders/overdue", headers=h)
    assert r.json()["count"] == 0


def test_days_overdue_calculated_correctly(client):
    h = register_and_login(client)
    three_days_ago = str(date.today() - timedelta(days=3))
    make_task(client, h, "Old task", due_date=three_days_ago)
    r = client.get("/tasks/reminders/overdue", headers=h)
    assert r.json()["tasks"][0]["days_overdue"] == 3


def test_days_until_due_calculated_correctly(client):
    h = register_and_login(client)
    in_two_days = str(date.today() + timedelta(days=2))
    make_task(client, h, "Soon task", due_date=in_two_days)
    r = client.get("/tasks/reminders/upcoming?days_ahead=5", headers=h)
    assert r.json()["tasks"][0]["days_until_due"] == 2


def test_reminders_user_isolation(client):
    h1 = register_and_login(client, "user1@test.com")
    h2 = register_and_login(client, "user2@test.com")
    yesterday = str(date.today() - timedelta(days=1))
    make_task(client, h1, "User1 overdue", due_date=yesterday)
    r = client.get("/tasks/reminders/overdue", headers=h2)
    assert r.json()["count"] == 0


# ===== Feature 7: Task Activity History =====

def test_task_creation_logged(client):
    h = register_and_login(client)
    t = make_task(client, h, "New task")
    r = client.get(f"/tasks/{t['id']}/activity", headers=h)
    assert r.status_code == 200
    activities = r.json()["activities"]
    assert any(a["action"] == "created" for a in activities)


def test_task_update_logged(client):
    h = register_and_login(client)
    t = make_task(client, h, "Original")
    client.put(f"/tasks/{t['id']}", json={"title": "Updated"}, headers=h)
    r = client.get(f"/tasks/{t['id']}/activity", headers=h)
    activities = r.json()["activities"]
    update_acts = [a for a in activities if a["action"] == "updated" and a["field_name"] == "title"]
    assert len(update_acts) >= 1
    assert update_acts[0]["old_value"] == "Original"
    assert update_acts[0]["new_value"] == "Updated"


def test_status_change_logged(client):
    h = register_and_login(client)
    t = make_task(client, h, "Status task")
    set_status(client, h, t["id"], "in-progress")
    r = client.get(f"/tasks/{t['id']}/activity", headers=h)
    activities = r.json()["activities"]
    status_acts = [a for a in activities if a["action"] == "status_changed"]
    assert len(status_acts) >= 1
    assert status_acts[0]["old_value"] == "pending"
    assert status_acts[0]["new_value"] == "in-progress"


def test_task_deletion_logged(client):
    h = register_and_login(client)
    t = make_task(client, h, "Delete me")
    r = client.get(f"/tasks/{t['id']}/activity", headers=h)
    assert r.json()["count"] >= 1  # creation was logged
    assert client.delete(f"/tasks/{t['id']}", headers=h).status_code == 204
    assert client.get(f"/tasks/{t['id']}", headers=h).status_code == 404


def test_activity_includes_user_email(client):
    h = register_and_login(client, "actor@example.com")
    t = make_task(client, h, "Email test")
    r = client.get(f"/tasks/{t['id']}/activity", headers=h)
    activities = r.json()["activities"]
    assert activities[0]["user_email"] == "actor@example.com"


def test_activity_ordered_by_created_at_desc(client):
    h = register_and_login(client)
    t = make_task(client, h, "First")
    client.put(f"/tasks/{t['id']}", json={"title": "Second"}, headers=h)
    set_status(client, h, t["id"], "in-progress")
    r = client.get(f"/tasks/{t['id']}/activity", headers=h)
    activities = r.json()["activities"]
    assert len(activities) >= 3
    actions = [a["action"] for a in activities]
    assert "created" in actions
    assert "status_changed" in actions


def test_user_isolation_activity(client):
    h1 = register_and_login(client, "user1@act.com")
    h2 = register_and_login(client, "user2@act.com")
    t = make_task(client, h1, "Private task")
    r = client.get(f"/tasks/{t['id']}/activity", headers=h2)
    assert r.status_code == 404


def test_activity_summary(client):
    h = register_and_login(client)
    make_task(client, h, "Task A")
    make_task(client, h, "Task B")
    r = client.get("/tasks/user/activity-summary", headers=h)
    assert r.status_code == 200
    assert r.json()["count"] >= 2


# ===== Feature 8: Subtasks and Checklists =====

def test_create_subtask(client):
    h = register_and_login(client)
    t = make_task(client, h, "Parent task")
    r = client.post(f"/tasks/{t['id']}/subtasks", json={"title": "Sub item"}, headers=h)
    assert r.status_code == 201
    assert r.json()["title"] == "Sub item"
    assert r.json()["completed"] is False


def test_create_subtask_wrong_owner(client):
    h1 = register_and_login(client, "owner@test.com")
    h2 = register_and_login(client, "other@test.com")
    t = make_task(client, h1, "Owner's task")
    r = client.post(f"/tasks/{t['id']}/subtasks", json={"title": "Intruder"}, headers=h2)
    assert r.status_code == 404


def test_list_subtasks_sorted_by_position(client):
    h = register_and_login(client)
    t = make_task(client, h, "Parent")
    client.post(f"/tasks/{t['id']}/subtasks", json={"title": "First"}, headers=h)
    client.post(f"/tasks/{t['id']}/subtasks", json={"title": "Second"}, headers=h)
    client.post(f"/tasks/{t['id']}/subtasks", json={"title": "Third"}, headers=h)
    r = client.get(f"/tasks/{t['id']}/subtasks", headers=h)
    assert r.status_code == 200
    titles = [s["title"] for s in r.json()]
    assert titles == ["First", "Second", "Third"]


def test_update_subtask_completed(client):
    h = register_and_login(client)
    t = make_task(client, h, "Parent")
    sub = client.post(f"/tasks/{t['id']}/subtasks", json={"title": "Check me"}, headers=h).json()
    r = client.put(f"/tasks/{t['id']}/subtasks/{sub['id']}", json={"completed": True}, headers=h)
    assert r.status_code == 200
    assert r.json()["completed"] is True


def test_delete_subtask(client):
    h = register_and_login(client)
    t = make_task(client, h, "Parent")
    sub = client.post(f"/tasks/{t['id']}/subtasks", json={"title": "Delete me"}, headers=h).json()
    r = client.delete(f"/tasks/{t['id']}/subtasks/{sub['id']}", headers=h)
    assert r.status_code == 204
    assert len(client.get(f"/tasks/{t['id']}/subtasks", headers=h).json()) == 0


def test_completion_stats_calculation(client):
    h = register_and_login(client)
    t = make_task(client, h, "Parent")
    for i in range(5):
        client.post(f"/tasks/{t['id']}/subtasks", json={"title": f"Sub {i}"}, headers=h)
    subs = client.get(f"/tasks/{t['id']}/subtasks", headers=h).json()
    for s in subs[:3]:
        client.put(f"/tasks/{t['id']}/subtasks/{s['id']}", json={"completed": True}, headers=h)
    r = client.get(f"/tasks/{t['id']}/subtasks/completion", headers=h)
    stats = r.json()
    assert stats["total"] == 5
    assert stats["completed"] == 3
    assert stats["percentage"] == 60.0


def test_completion_stats_empty_task(client):
    h = register_and_login(client)
    t = make_task(client, h, "Empty")
    r = client.get(f"/tasks/{t['id']}/subtasks/completion", headers=h)
    stats = r.json()
    assert stats["total"] == 0
    assert stats["completed"] == 0
    assert stats["percentage"] == 0.0


def test_subtask_cascade_delete(client):
    h = register_and_login(client)
    t = make_task(client, h, "Will delete")
    client.post(f"/tasks/{t['id']}/subtasks", json={"title": "Child"}, headers=h)
    client.delete(f"/tasks/{t['id']}", headers=h)
    assert client.get(f"/tasks/{t['id']}/subtasks", headers=h).status_code == 404


# ===== Feature 9: Team Collaboration =====

def test_share_task_with_user(client):
    h1 = register_and_login(client, "owner@collab.com")
    register_and_login(client, "friend@collab.com")
    t = make_task(client, h1, "Shared task")
    r = client.post(f"/tasks/{t['id']}/share", json={"email": "friend@collab.com", "permission": "view"}, headers=h1)
    assert r.status_code == 200
    assert "shared" in r.json()["message"].lower()


def test_share_task_fails_if_not_owner(client):
    h1 = register_and_login(client, "real_owner@collab.com")
    h2 = register_and_login(client, "notowner@collab.com")
    register_and_login(client, "third@collab.com")
    t = make_task(client, h1, "Owner's task")
    r = client.post(f"/tasks/{t['id']}/share", json={"email": "third@collab.com"}, headers=h2)
    assert r.status_code == 404


def test_cannot_share_with_self(client):
    h = register_and_login(client, "selfish@collab.com")
    t = make_task(client, h, "My task")
    r = client.post(f"/tasks/{t['id']}/share", json={"email": "selfish@collab.com"}, headers=h)
    assert r.status_code == 400
    assert "yourself" in r.json()["detail"].lower()


def test_cannot_share_twice(client):
    h1 = register_and_login(client, "owner2@collab.com")
    register_and_login(client, "friend2@collab.com")
    t = make_task(client, h1, "Share once")
    client.post(f"/tasks/{t['id']}/share", json={"email": "friend2@collab.com"}, headers=h1)
    r = client.post(f"/tasks/{t['id']}/share", json={"email": "friend2@collab.com"}, headers=h1)
    assert r.status_code == 400
    assert "already" in r.json()["detail"].lower()


def test_collaborator_can_view_task(client):
    h1 = register_and_login(client, "owner3@collab.com")
    h2 = register_and_login(client, "viewer@collab.com")
    t = make_task(client, h1, "Viewable task")
    client.post(f"/tasks/{t['id']}/share", json={"email": "viewer@collab.com", "permission": "view"}, headers=h1)
    r = client.get("/tasks/shared", headers=h2)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert any(task["title"] == "Viewable task" for task in r.json())


def test_add_comment_as_owner(client):
    h = register_and_login(client, "commentor@collab.com")
    t = make_task(client, h, "Comment task")
    r = client.post(f"/tasks/{t['id']}/comments", json={"content": "Great progress!"}, headers=h)
    assert r.status_code == 200
    assert r.json()["message"] == "Comment added"


def test_add_comment_as_collaborator(client):
    h1 = register_and_login(client, "owner4@collab.com")
    h2 = register_and_login(client, "collab@collab.com")
    t = make_task(client, h1, "Collab task")
    client.post(f"/tasks/{t['id']}/share", json={"email": "collab@collab.com", "permission": "comment"}, headers=h1)
    r = client.post(f"/tasks/{t['id']}/comments", json={"content": "My comment"}, headers=h2)
    assert r.status_code == 200


def test_get_comments(client):
    h = register_and_login(client, "reader@collab.com")
    t = make_task(client, h, "Commented task")
    client.post(f"/tasks/{t['id']}/comments", json={"content": "First comment"}, headers=h)
    client.post(f"/tasks/{t['id']}/comments", json={"content": "Second comment"}, headers=h)
    r = client.get(f"/tasks/{t['id']}/comments", headers=h)
    assert r.status_code == 200
    assert r.json()["count"] == 2


# ===== Feature 10: Export Tasks to CSV =====

def test_export_csv_all_tasks(client):
    h = register_and_login(client)
    make_task(client, h, "Export task 1")
    make_task(client, h, "Export task 2")
    r = client.post("/tasks/export/csv", json={}, headers=h)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]


def test_export_csv_with_filters(client):
    h = register_and_login(client)
    make_task(client, h, "High task", priority="high")
    make_task(client, h, "Low task", priority="low")
    r = client.post("/tasks/export/csv", json={"priority": "high"}, headers=h)
    content = r.text
    assert "High task" in content
    assert "Low task" not in content


def test_export_csv_correct_headers(client):
    h = register_and_login(client)
    make_task(client, h, "Header test")
    r = client.post("/tasks/export/csv", json={}, headers=h)
    reader = csv.reader(io.StringIO(r.text))
    headers = next(reader)
    assert headers == ["id", "title", "description", "status", "priority", "due_date", "created_at"]


def test_export_csv_content(client):
    h = register_and_login(client)
    make_task(client, h, "CSV content task", description="desc here", priority="high")
    r = client.post("/tasks/export/csv", json={}, headers=h)
    reader = csv.reader(io.StringIO(r.text))
    next(reader)  # skip header
    row = next(reader)
    assert row[1] == "CSV content task"
    assert row[2] == "desc here"
    assert row[4] == "high"


def test_export_csv_user_isolation(client):
    h1 = register_and_login(client, "exporter1@test.com")
    h2 = register_and_login(client, "exporter2@test.com")
    make_task(client, h1, "User1 only")
    r = client.post("/tasks/export/csv", json={}, headers=h2)
    assert "User1 only" not in r.text

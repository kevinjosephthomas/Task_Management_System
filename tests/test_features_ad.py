"""Tests for Features A-D: Enhanced Collaboration, Auth, DateTime, Reminders."""
from datetime import date, datetime, timedelta

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


def register_and_login(client, email="test@example.com", password="password123", username=None, full_name=None):
    if not username:
        username = email.split("@")[0].replace(".", "_")
        if len(username) < 3:
            username = username + "_user"
    payload = {"email": email, "password": password, "username": username}
    if full_name:
        payload["full_name"] = full_name
    client.post("/auth/register", json=payload)
    r = client.post("/auth/login", json={"email": email, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_task(client, headers, title="Task", description=None, priority="medium", due_date=None, due_datetime=None, assigned_to_email=None):
    payload = {"title": title, "description": description, "priority": priority}
    if due_date:
        payload["due_date"] = due_date
    if due_datetime:
        payload["due_datetime"] = due_datetime
    if assigned_to_email:
        payload["assigned_to_email"] = assigned_to_email
    r = client.post("/tasks/", json=payload, headers=headers)
    assert r.status_code == 201
    return r.json()


# ===== Feature A: Enhanced Team Collaboration =====

class TestTaskAssignment:
    def test_assign_task_to_user(self, client):
        h1 = register_and_login(client, "owner@test.com")
        register_and_login(client, "assignee@test.com")
        t = make_task(client, h1, "Assign me")
        r = client.post(f"/tasks/{t['id']}/assign", json={"email": "assignee@test.com"}, headers=h1)
        assert r.status_code == 200
        assert r.json()["assigned_to_email"] == "assignee@test.com"

    def test_assign_task_not_found(self, client):
        h = register_and_login(client, "owner2@test.com")
        r = client.post("/tasks/999/assign", json={"email": "someone@test.com"}, headers=h)
        assert r.status_code == 404

    def test_assign_task_user_not_found(self, client):
        h = register_and_login(client, "owner3@test.com")
        t = make_task(client, h, "Task")
        r = client.post(f"/tasks/{t['id']}/assign", json={"email": "nonexistent@test.com"}, headers=h)
        assert r.status_code == 400

    def test_create_task_with_assignment(self, client):
        h1 = register_and_login(client, "creator@test.com")
        register_and_login(client, "worker@test.com")
        t = make_task(client, h1, "Assigned task", assigned_to_email="worker@test.com")
        assert t["assigned_to_email"] == "worker@test.com"

    def test_get_assigned_tasks(self, client):
        h1 = register_and_login(client, "boss@test.com")
        h2 = register_and_login(client, "employee@test.com")
        make_task(client, h1, "Job 1", assigned_to_email="employee@test.com")
        make_task(client, h1, "Job 2", assigned_to_email="employee@test.com")
        r = client.get("/tasks/assigned", headers=h2)
        assert r.status_code == 200
        assert len(r.json()) == 2


class TestCollaborators:
    def test_add_collaborator(self, client):
        h1 = register_and_login(client, "lead@test.com")
        register_and_login(client, "dev@test.com")
        t = make_task(client, h1, "Team task")
        r = client.post(f"/tasks/{t['id']}/collaborators", json={"email": "dev@test.com", "role": "contributor"}, headers=h1)
        assert r.status_code == 200
        assert r.json()["role"] == "contributor"

    def test_cannot_add_self_as_collaborator(self, client):
        h = register_and_login(client, "solo@test.com")
        t = make_task(client, h, "My task")
        r = client.post(f"/tasks/{t['id']}/collaborators", json={"email": "solo@test.com", "role": "viewer"}, headers=h)
        assert r.status_code == 400
        assert "yourself" in r.json()["detail"].lower()

    def test_list_collaborators(self, client):
        h1 = register_and_login(client, "pm@test.com")
        register_and_login(client, "fe@test.com")
        register_and_login(client, "be@test.com")
        t = make_task(client, h1, "Project")
        client.post(f"/tasks/{t['id']}/collaborators", json={"email": "fe@test.com", "role": "contributor"}, headers=h1)
        client.post(f"/tasks/{t['id']}/collaborators", json={"email": "be@test.com", "role": "viewer"}, headers=h1)
        r = client.get(f"/tasks/{t['id']}/collaborators", headers=h1)
        assert r.status_code == 200
        assert r.json()["count"] == 2

    def test_remove_collaborator(self, client):
        h1 = register_and_login(client, "remover@test.com")
        register_and_login(client, "removee@test.com")
        t = make_task(client, h1, "Collab task")
        r = client.post(f"/tasks/{t['id']}/collaborators", json={"email": "removee@test.com"}, headers=h1)
        collab_id = r.json()["id"]
        r = client.delete(f"/tasks/{t['id']}/collaborators/{collab_id}", headers=h1)
        assert r.status_code == 204

    def test_update_collaborator_role(self, client):
        h1 = register_and_login(client, "updater@test.com")
        register_and_login(client, "updatee@test.com")
        t = make_task(client, h1, "Role task")
        client.post(f"/tasks/{t['id']}/collaborators", json={"email": "updatee@test.com", "role": "viewer"}, headers=h1)
        r = client.post(f"/tasks/{t['id']}/collaborators", json={"email": "updatee@test.com", "role": "manager"}, headers=h1)
        assert r.status_code == 200
        assert r.json()["role"] == "manager"

    def test_collaborator_can_access_comments(self, client):
        h1 = register_and_login(client, "commentowner@test.com")
        h2 = register_and_login(client, "commentcollab@test.com")
        t = make_task(client, h1, "Comment task")
        client.post(f"/tasks/{t['id']}/collaborators", json={"email": "commentcollab@test.com", "role": "contributor"}, headers=h1)
        r = client.post(f"/tasks/{t['id']}/comments", json={"content": "I can comment!"}, headers=h2)
        assert r.status_code == 200


class TestNotifications:
    def test_assignment_creates_notification(self, client):
        h1 = register_and_login(client, "notifier@test.com")
        h2 = register_and_login(client, "notified@test.com")
        make_task(client, h1, "Notify task", assigned_to_email="notified@test.com")
        r = client.get("/notifications", headers=h2)
        assert r.status_code == 200
        assert r.json()["count"] >= 1
        assert any("assigned" in n["type"] for n in r.json()["notifications"])

    def test_mark_notification_read(self, client):
        h1 = register_and_login(client, "sender@test.com")
        h2 = register_and_login(client, "receiver@test.com")
        make_task(client, h1, "Read test", assigned_to_email="receiver@test.com")
        r = client.get("/notifications?unread_only=true", headers=h2)
        notif_id = r.json()["notifications"][0]["id"]
        r = client.put(f"/notifications/{notif_id}/read", headers=h2)
        assert r.status_code == 200
        r = client.get("/notifications?unread_only=true", headers=h2)
        assert r.json()["count"] == 0

    def test_mark_all_notifications_read(self, client):
        h1 = register_and_login(client, "bulksender@test.com")
        h2 = register_and_login(client, "bulkreceiver@test.com")
        make_task(client, h1, "Bulk 1", assigned_to_email="bulkreceiver@test.com")
        make_task(client, h1, "Bulk 2", assigned_to_email="bulkreceiver@test.com")
        r = client.put("/notifications/read-all", headers=h2)
        assert r.status_code == 200
        r = client.get("/notifications?unread_only=true", headers=h2)
        assert r.json()["count"] == 0

    def test_collaborator_add_creates_notification(self, client):
        h1 = register_and_login(client, "collabnotif_owner@test.com")
        h2 = register_and_login(client, "collabnotif_user@test.com")
        t = make_task(client, h1, "Collab notif task")
        client.post(f"/tasks/{t['id']}/collaborators", json={"email": "collabnotif_user@test.com", "role": "contributor"}, headers=h1)
        r = client.get("/notifications", headers=h2)
        assert any("collaborator" in n["type"] for n in r.json()["notifications"])


# ===== Feature B: Enhanced Authentication =====

class TestEnhancedAuth:
    def test_register_with_username(self, client):
        r = client.post("/auth/register", json={
            "email": "username@test.com",
            "password": "password123",
            "username": "cooluser",
            "full_name": "Cool User",
        })
        assert r.status_code == 201
        assert r.json()["username"] == "cooluser"
        assert r.json()["full_name"] == "Cool User"

    def test_register_duplicate_username(self, client):
        client.post("/auth/register", json={
            "email": "first@test.com", "password": "password123", "username": "taken",
        })
        r = client.post("/auth/register", json={
            "email": "second@test.com", "password": "password123", "username": "taken",
        })
        assert r.status_code == 400
        assert "taken" in r.json()["detail"].lower()

    def test_get_profile(self, client):
        h = register_and_login(client, "profile@test.com", username="profuser", full_name="Prof User")
        r = client.get("/auth/profile", headers=h)
        assert r.status_code == 200
        assert r.json()["email"] == "profile@test.com"
        assert r.json()["username"] == "profuser"
        assert r.json()["full_name"] == "Prof User"

    def test_update_profile(self, client):
        h = register_and_login(client, "updateprof@test.com")
        r = client.put("/auth/profile", json={
            "full_name": "Updated Name",
            "bio": "I am a developer",
            "timezone": "US/Pacific",
        }, headers=h)
        assert r.status_code == 200
        assert r.json()["full_name"] == "Updated Name"
        assert r.json()["bio"] == "I am a developer"
        assert r.json()["timezone"] == "US/Pacific"

    def test_update_profile_duplicate_username(self, client):
        register_and_login(client, "first_u@test.com", username="existing")
        h2 = register_and_login(client, "second_u@test.com")
        r = client.put("/auth/profile", json={"username": "existing"}, headers=h2)
        assert r.status_code == 400

    def test_google_auth_not_configured(self, client):
        r = client.post("/auth/google", json={"token": "fake-token"})
        assert r.status_code in (501, 401)

    def test_list_timezones(self, client):
        r = client.get("/auth/timezones")
        assert r.status_code == 200
        assert "UTC" in r.json()["timezones"]


# ===== Feature C: DateTime and Deadline Support =====

class TestDateTimeSupport:
    def test_create_task_with_due_datetime(self, client):
        h = register_and_login(client, "dt@test.com")
        future = (datetime.utcnow() + timedelta(hours=48)).isoformat()
        t = make_task(client, h, "DateTime task", due_datetime=future)
        assert t["due_datetime"] is not None

    def test_task_deadline_info(self, client):
        h = register_and_login(client, "deadline@test.com")
        future = (datetime.utcnow() + timedelta(hours=5)).isoformat()
        t = make_task(client, h, "Deadline task", due_datetime=future)
        assert t["deadline_info"] is not None
        assert t["deadline_info"]["is_past_due"] is False

    def test_task_deadline_endpoint(self, client):
        h = register_and_login(client, "deadlineep@test.com")
        future = (datetime.utcnow() + timedelta(hours=10)).isoformat()
        t = make_task(client, h, "Endpoint task", due_datetime=future)
        r = client.get(f"/tasks/{t['id']}/deadline", headers=h)
        assert r.status_code == 200
        assert r.json()["deadline_info"] is not None

    def test_overdue_datetime_detection(self, client):
        h = register_and_login(client, "overduedt@test.com")
        past = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        t = make_task(client, h, "Past task", due_datetime=past)
        assert t["is_overdue"] is True
        assert t["deadline_info"]["is_past_due"] is True

    def test_update_task_due_datetime(self, client):
        h = register_and_login(client, "updatedt@test.com")
        t = make_task(client, h, "Update DT task")
        future = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        r = client.put(f"/tasks/{t['id']}", json={"due_datetime": future}, headers=h)
        assert r.status_code == 200
        assert r.json()["due_datetime"] is not None


# ===== Feature D: Automated Reminder System =====

class TestReminderSystem:
    def test_scheduler_functions_importable(self, client):
        from app.scheduler import check_deadlines, check_overdue
        assert callable(check_deadlines)
        assert callable(check_overdue)

    def test_notification_email_functions_importable(self, client):
        from app.notifications import (
            task_assigned_email, deadline_reminder_email, overdue_alert_email
        )
        assert callable(task_assigned_email)
        assert callable(deadline_reminder_email)
        assert callable(overdue_alert_email)

    def test_email_disabled_by_default(self, client):
        from app.notifications import EMAIL_ENABLED, send_email
        assert EMAIL_ENABLED is False
        result = send_email("test@test.com", "Test", "<p>Test</p>")
        assert result is False

    def test_utils_deadline_countdown(self, client):
        from app.utils import format_deadline_countdown
        future = datetime.utcnow() + timedelta(hours=5, minutes=30)
        info = format_deadline_countdown(future)
        assert info["is_past_due"] is False
        assert info["hours"] >= 5

        past = datetime.utcnow() - timedelta(days=2)
        info = format_deadline_countdown(past)
        assert info["is_past_due"] is True
        assert info["days"] >= 1

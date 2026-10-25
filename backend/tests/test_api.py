from sqlalchemy import select
from app.models import Application, ApplicationStage, AuditLog, User

PASSWORD = "TestPassword123!"


def token_for(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_failure(client):
    response = client.post("/api/auth/login", json={"email": "institution1@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_institution_can_create_application_and_audit_is_written(client, test_db):
    token = token_for(client, "institution1@example.com")
    response = client.post("/api/applications", headers=headers(token), json={"title": "Synthetic engineering application", "description": "Fictional test data"})
    assert response.status_code == 201, response.text
    app_data = response.json()
    assert app_data["current_stage"] == "SUBMITTED"
    assert test_db.scalar(select(ApplicationStage).where(ApplicationStage.application_id == app_data["id"])) is not None
    assert test_db.scalar(select(AuditLog).where(AuditLog.entity_id == app_data["id"], AuditLog.action == "APPLICATION_SUBMITTED")) is not None


def test_one_institution_cannot_read_another_institutions_application(client):
    token_one = token_for(client, "institution1@example.com")
    token_two = token_for(client, "institution2@example.com")
    created = client.post("/api/applications", headers=headers(token_one), json={"title": "Institution One case"})
    app_id = created.json()["id"]
    response = client.get(f"/api/applications/{app_id}", headers=headers(token_two))
    assert response.status_code == 404


def test_institution_cannot_transition_application(client):
    token = token_for(client, "institution1@example.com")
    created = client.post("/api/applications", headers=headers(token), json={"title": "No transition case"})
    app_id = created.json()["id"]
    response = client.post(f"/api/applications/{app_id}/transition", headers=headers(token), json={"to_stage": "INITIAL_SCRUTINY"})
    assert response.status_code == 403


def test_invalid_transition_is_rejected(client, test_db):
    institution_token = token_for(client, "institution1@example.com")
    created = client.post("/api/applications", headers=headers(institution_token), json={"title": "Invalid stage case"})
    app_id = created.json()["id"]
    officer = test_db.scalar(select(User).where(User.email == "officer@example.com"))
    application = test_db.get(Application, app_id)
    application.assigned_officer_id = officer.id
    test_db.commit()
    officer_token = token_for(client, "officer@example.com")
    response = client.post(f"/api/applications/{app_id}/transition", headers=headers(officer_token), json={"to_stage": "APPROVED", "note": "Skipping stages is not allowed"})
    assert response.status_code == 422


def test_admin_can_assign_officer_and_officer_can_view(client, test_db):
    institution_token = token_for(client, "institution1@example.com")
    created = client.post("/api/applications", headers=headers(institution_token), json={"title": "Assignment test case"})
    app_id = created.json()["id"]
    admin_token = token_for(client, "admin@example.com")
    officer = test_db.scalar(select(User).where(User.email == "officer@example.com"))
    assigned = client.patch(f"/api/applications/{app_id}/assignment", headers=headers(admin_token),
                            json={"assigned_officer_id": officer.id})
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["assigned_officer_id"] == officer.id
    officer_token = token_for(client, "officer@example.com")
    visible = client.get(f"/api/applications/{app_id}", headers=headers(officer_token))
    assert visible.status_code == 200


def test_application_history_includes_submission_event(client):
    institution_token = token_for(client, "institution1@example.com")
    created = client.post("/api/applications", headers=headers(institution_token), json={"title": "History test case"})
    app_id = created.json()["id"]
    history = client.get(f"/api/applications/{app_id}/history", headers=headers(institution_token))
    assert history.status_code == 200, history.text
    assert [item["to_stage"] for item in history.json()["stages"]] == ["SUBMITTED"]
    assert any(item["action"] == "APPLICATION_SUBMITTED" for item in history.json()["audit_events"])


def test_query_and_response_are_recorded(client):
    token = token_for(client, "institution1@example.com")
    created = client.post("/api/applications", headers=headers(token), json={"title": "Query test case"})
    app_id = created.json()["id"]
    query = client.post(f"/api/applications/{app_id}/queries", headers=headers(token),
                        json={"message": "Please clarify this synthetic test field"})
    assert query.status_code == 201, query.text
    query_id = query.json()["id"]
    response = client.post(f"/api/queries/{query_id}/responses", headers=headers(token),
                           json={"message": "Synthetic clarification supplied"})
    assert response.status_code == 201, response.text
    assert response.json()["query_id"] == query_id

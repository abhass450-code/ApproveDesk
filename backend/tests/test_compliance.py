from app.models.compliance import ComplianceRule
from app.services.compliance_service import evaluate_rule


def _rule(**kwargs) -> ComplianceRule:
    defaults = dict(code="T-1", name="Test", field_key="faculty_count", operator=">=",
                    threshold_value=20, unit="faculty", severity="HIGH", demo_only=True)
    defaults.update(kwargs)
    return ComplianceRule(**defaults)


def test_evaluate_above_equal_below_threshold():
    assert evaluate_rule(_rule(), {"faculty_count": 22})["status"] == "PASS"
    assert evaluate_rule(_rule(), {"faculty_count": 20})["status"] == "PASS"
    fail = evaluate_rule(_rule(), {"faculty_count": 18})
    assert fail["status"] == "FAIL"
    assert fail["gap"] == 2


def test_evaluate_missing_and_non_numeric_fields():
    assert evaluate_rule(_rule(), {})["status"] == "NEEDS_REVIEW"
    assert evaluate_rule(_rule(), {"faculty_count": "abc"})["status"] == "NEEDS_REVIEW"
    assert evaluate_rule(_rule(operator="exists"), {"faculty_count": None})["status"] == "NEEDS_REVIEW"
    assert evaluate_rule(_rule(operator="exists"), {"faculty_count": 5})["status"] == "PASS"


def login(client, email):
    res = client.post("/api/auth/login", json={"email": email, "password": "TestPassword123!"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_rule_admin_lifecycle_and_check_flow(client):
    admin = login(client, "admin@example.com")
    officer_token = login(client, "officer@example.com")
    institution = login(client, "institution1@example.com")

    # non-admin cannot create rules
    res = client.post("/api/compliance/rules", headers=auth(officer_token),
                      json={"code": "X", "name": "X", "field_key": "f", "operator": ">=", "threshold_value": 1})
    assert res.status_code == 403

    # invalid operator rejected
    res = client.post("/api/compliance/rules", headers=auth(admin),
                      json={"code": "BAD-1", "name": "Bad", "field_key": "f", "operator": "~~", "threshold_value": 1})
    assert res.status_code == 422

    res = client.post("/api/compliance/rules", headers=auth(admin),
                      json={"code": "DEMO-FACULTY-001", "name": "Faculty", "field_key": "faculty_count",
                            "operator": ">=", "threshold_value": 20, "severity": "HIGH", "demo_only": True})
    assert res.status_code == 201, res.text

    # institution creates application; admin assigns officer
    res = client.post("/api/applications", headers=auth(institution),
                      json={"title": "Golden case", "submitted_data": {"faculty_count": 18}})
    assert res.status_code == 201, res.text
    app_id = res.json()["id"]

    officers = client.get("/api/users/officers", headers=auth(admin)).json()
    officer_id = officers[0]["id"]
    res = client.patch(f"/api/applications/{app_id}/assignment", headers=auth(admin),
                       json={"assigned_officer_id": officer_id})
    assert res.status_code == 200

    # move to COMPLIANCE_CHECK
    for stage in ("INITIAL_SCRUTINY", "DOCUMENT_VERIFICATION", "COMPLIANCE_CHECK"):
        res = client.post(f"/api/applications/{app_id}/transition", headers=auth(officer_token),
                          json={"to_stage": stage})
        assert res.status_code == 200, res.text

    res = client.post(f"/api/applications/{app_id}/compliance/check", headers=auth(officer_token))
    assert res.status_code == 200
    body = res.json()
    assert body["summary"]["failed"] == 1
    assert body["results"][0]["status"] == "FAIL"
    assert body["results"][0]["gap"] == 2

    # institution corrects data; recheck passes; both runs remain traceable
    res = client.patch(f"/api/applications/{app_id}/data", headers=auth(institution),
                       json={"submitted_data": {"faculty_count": 22}})
    assert res.status_code == 200
    res = client.post(f"/api/applications/{app_id}/compliance/check", headers=auth(officer_token))
    assert res.json()["summary"]["passed"] == 1

    res = client.get(f"/api/applications/{app_id}/compliance/results", headers=auth(institution))
    assert len(res.json()) == 2
    statuses = [item["status"] for item in res.json()]
    assert "FAIL" in statuses and "PASS" in statuses

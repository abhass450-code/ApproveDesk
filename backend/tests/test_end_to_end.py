"""Golden scenario (Master Blueprint section 13): submit -> assign -> stage -> rule FAIL ->
alert -> query -> correction -> re-check PASS. Repeatable on a fresh test DB."""
from tests.test_compliance import auth, login


def test_golden_scenario(client):
    admin = login(client, "admin@example.com")
    officer_token = login(client, "officer@example.com")
    institution = login(client, "institution1@example.com")

    # 1-2. institution submits application with sample data
    res = client.post("/api/applications", headers=auth(institution),
                      json={"title": "Golden scenario case",
                            "submitted_data": {"faculty_count": 18, "infrastructure_capacity": 120}})
    assert res.status_code == 201, res.text
    app_id = res.json()["id"]

    # 3. admin assigns officer
    officer_id = client.get("/api/users/officers", headers=auth(admin)).json()[0]["id"]
    assert client.patch(f"/api/applications/{app_id}/assignment", headers=auth(admin),
                        json={"assigned_officer_id": officer_id}).status_code == 200

    # 4. workflow advances to COMPLIANCE_CHECK
    for stage in ("INITIAL_SCRUTINY", "DOCUMENT_VERIFICATION", "COMPLIANCE_CHECK"):
        assert client.post(f"/api/applications/{app_id}/transition", headers=auth(officer_token),
                           json={"to_stage": stage}).status_code == 200

    # 5. sample rule fails (18 < 20)
    client.post("/api/compliance/rules", headers=auth(admin),
                json={"code": "DEMO-FACULTY-001", "name": "Faculty", "field_key": "faculty_count",
                      "operator": ">=", "threshold_value": 20, "severity": "HIGH", "demo_only": True})
    res = client.post(f"/api/applications/{app_id}/compliance/check", headers=auth(officer_token))
    assert res.json()["summary"]["failed"] == 1

    # 6. failure alert exists; scans stay deduplicated
    alerts = client.get("/api/alerts", headers=auth(officer_token)).json()
    assert any(a["alert_type"] == "COMPLIANCE_FAILURE" and a["application_id"] == app_id for a in alerts)
    first = client.post("/api/alerts/scan", headers=auth(admin)).json()
    second = client.post("/api/alerts/scan", headers=auth(admin)).json()
    assert second["created"] == 0

    # 7-8. officer queries; institution responds and corrects the data
    res = client.post(f"/api/applications/{app_id}/queries", headers=auth(officer_token),
                      json={"message": "Submit corrected faculty evidence."})
    query_id = res.json()["id"]
    assert client.post(f"/api/queries/{query_id}/responses", headers=auth(institution),
                       json={"message": "Corrected roster uploaded; count updated."}).status_code == 201
    assert client.patch(f"/api/applications/{app_id}/data", headers=auth(institution),
                        json={"submitted_data": {"faculty_count": 22, "infrastructure_capacity": 120}}).status_code == 200

    # 9. re-check passes; history preserved
    res = client.post(f"/api/applications/{app_id}/compliance/check", headers=auth(officer_token))
    assert res.json()["summary"]["passed"] == 1
    results = client.get(f"/api/applications/{app_id}/compliance/results", headers=auth(officer_token)).json()
    assert len(results) == 2

    # 10. authorized transition + audit trail present
    assert client.post(f"/api/applications/{app_id}/transition", headers=auth(officer_token),
                       json={"to_stage": "OFFICER_REVIEW"}).status_code == 200
    history = client.get(f"/api/applications/{app_id}/history", headers=auth(officer_token)).json()
    assert any(event["action"] == "COMPLIANCE_CHECK_RUN" for event in history["audit_events"])
    assert len(history["stages"]) >= 5

    # 11. assistant explains from records without an AI key
    res = client.post("/api/chat/messages", headers=auth(institution),
                      json={"message": "Why did compliance fail?", "application_id": app_id})
    body = res.json()
    assert body["used_ai"] is False
    assert "DEMO-FACULTY-001" in body["answer"]

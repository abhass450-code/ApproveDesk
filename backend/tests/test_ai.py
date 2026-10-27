from tests.test_compliance import auth, login


def _create_application(client, institution_token):
    res = client.post("/api/applications", headers=auth(institution_token),
                      json={"title": "AI test case", "submitted_data": {"faculty_count": 10}})
    assert res.status_code == 201
    return res.json()["id"]


def test_chat_answers_from_records_without_ai_key(client):
    institution = login(client, "institution1@example.com")
    app_id = _create_application(client, institution)

    res = client.post("/api/chat/messages", headers=auth(institution),
                      json={"message": "Why is my application pending?", "application_id": app_id})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["used_ai"] is False
    assert "SUBMITTED" in body["answer"]
    assert len(body["sources"]) >= 1

    res = client.post("/api/chat/messages", headers=auth(institution),
                      json={"message": "What should I do next?", "application_id": app_id})
    assert len(res.json()["suggested_actions"]) >= 1

    # conversation persisted
    res = client.get(f"/api/chat/conversations/{body['conversation_id']}/messages", headers=auth(institution))
    assert len(res.json()) == 2


def test_chat_cannot_access_other_institution_records(client):
    institution = login(client, "institution1@example.com")
    other = login(client, "institution2@example.com")
    app_id = _create_application(client, institution)

    res = client.post("/api/chat/messages", headers=auth(other),
                      json={"message": "status?", "application_id": app_id})
    assert res.status_code == 404


def test_summary_endpoint_deterministic(client):
    institution = login(client, "institution1@example.com")
    app_id = _create_application(client, institution)
    res = client.get(f"/api/applications/{app_id}/summary", headers=auth(institution))
    assert res.status_code == 200
    body = res.json()
    assert body["generated_by"] == "deterministic"
    assert "SUBMITTED" in body["summary"]

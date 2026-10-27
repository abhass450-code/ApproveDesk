from datetime import datetime, timedelta, timezone

from tests.test_compliance import auth, login


def test_overdue_alert_created_once_and_acknowledged(client):
    admin = login(client, "admin@example.com")
    officer_token = login(client, "officer@example.com")
    institution = login(client, "institution1@example.com")

    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    res = client.post("/api/applications", headers=auth(institution),
                      json={"title": "Overdue case", "due_at": past})
    app_id = res.json()["id"]
    officer_id = client.get("/api/users/officers", headers=auth(admin)).json()[0]["id"]
    client.patch(f"/api/applications/{app_id}/assignment", headers=auth(admin),
                 json={"assigned_officer_id": officer_id})

    res = client.post("/api/alerts/scan", headers=auth(admin))
    assert res.status_code == 200
    assert res.json()["created"] >= 1

    # repeat scan must not duplicate unresolved alerts
    res = client.post("/api/alerts/scan", headers=auth(admin))
    assert res.json()["created"] == 0
    assert res.json()["skipped"] >= 1

    alerts = client.get("/api/alerts", headers=auth(officer_token)).json()
    overdue = [a for a in alerts if a["alert_type"] == "OVERDUE_STAGE" and a["application_id"] == app_id]
    assert len(overdue) == 1

    res = client.post(f"/api/alerts/{overdue[0]['id']}/acknowledge", headers=auth(officer_token))
    assert res.status_code == 200
    assert res.json()["status"] == "ACKNOWLEDGED"

    # another institution cannot acknowledge this alert
    other = login(client, "institution2@example.com")
    res = client.post(f"/api/alerts/{overdue[0]['id']}/acknowledge", headers=auth(other))
    assert res.status_code == 404


def test_deadline_soon_alert_and_scan_permission(client):
    admin = login(client, "admin@example.com")
    institution = login(client, "institution1@example.com")
    soon = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
    res = client.post("/api/applications", headers=auth(institution),
                      json={"title": "Due soon case", "due_at": soon})
    assert res.status_code == 201, res.text

    res = client.post("/api/alerts/scan", headers=auth(admin))
    assert res.status_code == 200

    alerts = client.get("/api/alerts", headers=auth(institution)).json()
    assert any(a["alert_type"] == "DEADLINE_SOON" for a in alerts)

    # institution cannot run the admin scan
    res = client.post("/api/alerts/scan", headers=auth(institution))
    assert res.status_code == 403

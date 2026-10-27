import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.alert import Base, Alert, AlertStatus, AlertType, AlertSeverity
from app.schemas.alert import AlertCreate
from app.services import alert_service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_deduplication_prevention(db_session):
    now = datetime.now(timezone.utc)
    alert_in = AlertCreate(
        application_id="APP-TEST-1",
        recipient_id="INST-1",
        alert_type=AlertType.DEADLINE_SOON,
        severity=AlertSeverity.MEDIUM,
        message="Test alert",
        due_at=now + timedelta(hours=5),
        dedupe_key="DEADLINE_SOON:APP-TEST-1:STAGE-1:20261027"
    )

    # First insertion creates new alert
    alert1, created1 = alert_service.create_or_update_alert(db_session, alert_in)
    assert created1 is True
    assert db_session.query(Alert).count() == 1

    # Second scan with same dedupe_key updates instead of creating duplicate
    alert2, created2 = alert_service.create_or_update_alert(db_session, alert_in)
    assert created2 is False
    assert db_session.query(Alert).count() == 1
    assert alert1.id == alert2.id


def test_scan_and_create_alerts_rules(db_session):
    now = datetime.now(timezone.utc)
    test_apps = [
        {
            "id": "APP-DUE-SOON",
            "recipient_id": "INST-1",
            "stage": "STAGE_1",
            "due_at": now + timedelta(hours=10),
            "is_completed": False
        },
        {
            "id": "APP-OVERDUE",
            "recipient_id": "OFFICER-1",
            "stage": "STAGE_2",
            "due_at": now - timedelta(hours=2),
            "is_completed": False
        }
    ]

    result = alert_service.scan_and_create_alerts(db_session, test_apps)
    assert result["created_count"] == 2

    due_soon_alert = db_session.query(Alert).filter(Alert.application_id == "APP-DUE-SOON").first()
    assert due_soon_alert.alert_type == AlertType.DEADLINE_SOON

    overdue_alert = db_session.query(Alert).filter(Alert.application_id == "APP-OVERDUE").first()
    assert overdue_alert.alert_type == AlertType.OVERDUE_STAGE


def test_acknowledge_alert_security(db_session):
    now = datetime.now(timezone.utc)
    alert_in = AlertCreate(
        application_id="APP-TEST-2",
        recipient_id="INST-OWNER",
        alert_type=AlertType.COMPLIANCE_FAILURE,
        severity=AlertSeverity.HIGH,
        message="Compliance Error",
        due_at=now,
        dedupe_key="COMPLIANCE:APP-TEST-2:RULE-1"
    )
    alert, _ = alert_service.create_or_update_alert(db_session, alert_in)

    # Unauthorized user attempting to acknowledge should fail
    unauthorized = alert_service.acknowledge_alert(db_session, alert.id, recipient_id="OTHER-USER", is_admin=False)
    assert unauthorized is None

    # Authorized recipient acknowledges successfully
    authorized = alert_service.acknowledge_alert(db_session, alert.id, recipient_id="INST-OWNER", is_admin=False)
    assert authorized is not None
    assert authorized.status == AlertStatus.ACKNOWLEDGED
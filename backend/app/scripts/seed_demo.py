"""Seed synthetic demo accounts and the repeatable golden scenario.

Fictional/demo data only. The demo rule values are sample assumptions,
NOT official AICTE requirements (Master Blueprint, regulatory guardrail).
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.application import Application
from app.models.application_stage import ApplicationStage
from app.models.compliance import ComplianceResult, ComplianceRule
from app.models.document import Document
from app.models.institution import Institution
from app.models.query import Query, QueryResponse
from app.models.user import User
from app.services.alert_service import create_compliance_failure_alert, scan_alerts
from app.services.audit_service import append_audit
from app.services.compliance_service import evaluate_rule

DEMO_PASSWORD = "Demo-Only-ChangeMe-2026!"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_accounts(db) -> tuple[Institution, User, User, User]:
    institution = db.scalar(select(Institution).where(Institution.institution_code == "DEMO-INST-001"))
    if institution is None:
        institution = Institution(institution_code="DEMO-INST-001", name="Demo Engineering Institute", state="Demo State")
        db.add(institution)
        db.flush()

    accounts = [
        ("institution.demo@example.com", "Demo Institution User", "INSTITUTION", institution.id),
        ("officer.demo@example.com", "Demo Review Officer", "OFFICER", None),
        ("admin.demo@example.com", "Demo System Admin", "ADMIN", None),
    ]
    users: dict[str, User] = {}
    for email, name, role, institution_id in accounts:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, full_name=name, role=role, institution_id=institution_id,
                        password_hash=hash_password(DEMO_PASSWORD), is_active=True)
            db.add(user)
            db.flush()
        users[role] = user
    return institution, users["INSTITUTION"], users["OFFICER"], users["ADMIN"]


def _delete_application(db, app: Application) -> None:
    for query in db.scalars(select(Query).where(Query.application_id == app.id)).all():
        for response in db.scalars(select(QueryResponse).where(QueryResponse.query_id == query.id)).all():
            db.delete(response)
        db.delete(query)
    for model in (Alert, ComplianceResult, Document, ApplicationStage):
        for row in db.scalars(select(model).where(model.application_id == app.id)).all():
            db.delete(row)
    db.delete(app)


def ensure_rules(db) -> tuple[ComplianceRule, ComplianceRule]:
    def upsert(code: str, name: str, field_key: str, threshold: float, unit: str, severity: str) -> ComplianceRule:
        rule = db.scalar(select(ComplianceRule).where(ComplianceRule.code == code))
        if rule is None:
            rule = ComplianceRule(code=code, name=name, category="MINIMUM_REQUIREMENT", field_key=field_key,
                                  operator=">=", threshold_value=threshold, unit=unit, severity=severity,
                                  active=True, version=1, demo_only=True,
                                  description="Sample rule for prototype demonstration only. "
                                              "NOT a verified official AICTE requirement.")
            db.add(rule)
            db.flush()
        return rule

    faculty = upsert("DEMO-FACULTY-001", "Faculty strength (sample)", "faculty_count", 20, "faculty members", "HIGH")
    infra = upsert("DEMO-INFRA-001", "Infrastructure capacity (sample)", "infrastructure_capacity", 100,
                   "seats", "MEDIUM")
    return faculty, infra


def reset_scenario(db, institution: Institution, institution_user: User, officer: User) -> None:
    for code in ("DEMO-APP-0001", "DEMO-APP-0002"):
        existing = db.scalar(select(Application).where(Application.application_code == code))
        if existing is not None:
            _delete_application(db, existing)
    db.flush()

    faculty_rule, infra_rule = ensure_rules(db)
    now = _utcnow()

    app1 = Application(
        application_code="DEMO-APP-0001", institution_id=institution.id, created_by_id=institution_user.id,
        assigned_officer_id=officer.id, title="Approval for new B.Tech programme 2026-27",
        description="Synthetic golden-scenario application for the repeatable demo.",
        current_stage="COMPLIANCE_CHECK",
        submitted_data={"application_type": "NEW_PROGRAMME", "academic_year": "2026-27",
                        "programme": "B.Tech Computer Science", "faculty_count": 18,
                        "infrastructure_capacity": 120},
        due_at=now + timedelta(hours=12))
    app2 = Application(
        application_code="DEMO-APP-0002", institution_id=institution.id, created_by_id=institution_user.id,
        assigned_officer_id=officer.id, title="Extension of existing approval",
        description="Synthetic overdue case used to demonstrate the alert engine.",
        current_stage="INITIAL_SCRUTINY",
        submitted_data={"application_type": "EXTENSION", "academic_year": "2026-27",
                        "programme": "B.Tech Mechanical", "faculty_count": 25,
                        "infrastructure_capacity": 90},
        due_at=now - timedelta(days=2))
    db.add_all([app1, app2])
    db.flush()

    # stage history for the golden scenario case
    history = [
        (app1, None, "SUBMITTED", institution_user.id, "Application submitted"),
        (app1, "SUBMITTED", "INITIAL_SCRUTINY", officer.id, "Accepted for initial scrutiny"),
        (app1, "INITIAL_SCRUTINY", "DOCUMENT_VERIFICATION", officer.id, "Documents routed for verification"),
        (app1, "DOCUMENT_VERIFICATION", "COMPLIANCE_CHECK", officer.id, "Routed to compliance check"),
        (app2, None, "SUBMITTED", institution_user.id, "Application submitted"),
        (app2, "SUBMITTED", "INITIAL_SCRUTINY", officer.id, "Accepted for initial scrutiny"),
    ]
    for app, from_stage, to_stage, actor_id, note in history:
        db.add(ApplicationStage(application_id=app.id, from_stage=from_stage, to_stage=to_stage,
                                changed_by_id=actor_id, note=note))

    # synthetic document placeholder
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    placeholder = settings.upload_dir / "DEMO-APP-0001-faculty-list-demo.txt"
    placeholder.write_text("Synthetic demo faculty roster. Not a real document.\n", encoding="utf-8")
    doc = Document(application_id=app1.id, filename="faculty-list-demo.txt", content_type="text/plain",
                   storage_path=str(placeholder), uploaded_by_id=institution_user.id, verified=False)
    db.add(doc)
    db.flush()

    # evaluate app1 against the sample rules; persist results + failure alert
    for rule in (faculty_rule, infra_rule):
        outcome = evaluate_rule(rule, app1.submitted_data)
        result = ComplianceResult(
            application_id=app1.id, rule_id=rule.id, rule_code=rule.code, rule_version=rule.version,
            field_key=rule.field_key, expected=outcome["expected"], actual=outcome["actual"], unit=rule.unit,
            status=outcome["status"], gap=outcome["gap"], explanation=outcome["explanation"],
            evidence_document_ids=[doc.id] if rule.field_key == "faculty_count" else [])
        db.add(result)
        if outcome["status"] == "FAIL":
            create_compliance_failure_alert(db, app1, rule, outcome)

    # open officer query awaiting institution response
    db.add(Query(application_id=app1.id, raised_by_id=officer.id,
                 message="Please submit corrected faculty evidence. The recorded faculty_count is 18 while the "
                         "sample rule expects at least 20. Upload a corrected roster and update the declared count.",
                 due_at=now + timedelta(days=2), status="OPEN"))

    append_audit(db, actor_id=officer.id, action="DEMO_SCENARIO_RESET", entity_type="system",
                 entity_id=None, details={"applications": ["DEMO-APP-0001", "DEMO-APP-0002"]})
    scan_alerts(db, officer)  # creates DEADLINE_SOON (app1) and OVERDUE_STAGE (app2)
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        institution, institution_user, officer, _admin = ensure_accounts(db)
        reset_scenario(db, institution, institution_user, officer)
        db.commit()
    print("Synthetic demo accounts and golden scenario are ready.")
    print("  institution.demo@example.com  (INSTITUTION)")
    print("  officer.demo@example.com      (OFFICER)")
    print("  admin.demo@example.com        (ADMIN)")
    print("Local-only demo password for all three: Demo-Only-ChangeMe-2026!")
    print("Never deploy with these credentials.")


if __name__ == "__main__":
    main()

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.compliance import ComplianceRule, ComplianceResult
from app.models.user import User
from app.services.audit_service import append_audit

ALLOWED_OPERATORS = (">=", "<=", "==", "!=", "exists")


def evaluate_rule(rule: ComplianceRule, submitted_data: dict | None) -> dict:
    """Deterministic rule evaluation. Never uses eval(); unknown/missing data -> NEEDS_REVIEW."""
    data = submitted_data or {}
    raw = data.get(rule.field_key)

    if rule.operator == "exists":
        present = raw is not None and raw != ""
        return {
            "status": "PASS" if present else "NEEDS_REVIEW",
            "expected": "exists",
            "actual": raw,
            "gap": None,
            "explanation": f"Field '{rule.field_key}' is {'present' if present else 'missing or empty'}.",
        }

    if raw is None:
        return {"status": "NEEDS_REVIEW", "expected": rule.threshold_value, "actual": None, "gap": None,
                "explanation": f"Field '{rule.field_key}' is missing from the submitted data."}
    try:
        actual = float(raw)
    except (TypeError, ValueError):
        return {"status": "NEEDS_REVIEW", "expected": rule.threshold_value, "actual": raw, "gap": None,
                "explanation": f"Field '{rule.field_key}' value {raw!r} is not numeric; human review needed."}
    try:
        expected = float(rule.threshold_value)
    except (TypeError, ValueError):
        return {"status": "NEEDS_REVIEW", "expected": rule.threshold_value, "actual": actual, "gap": None,
                "explanation": "Rule threshold is not numeric; rule configuration needs review."}

    if rule.operator == ">=":
        passed = actual >= expected
    elif rule.operator == "<=":
        passed = actual <= expected
    elif rule.operator == "==":
        passed = actual == expected
    elif rule.operator == "!=":
        passed = actual != expected
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Unsupported operator: {rule.operator}")

    gap = round(expected - actual, 4) if (rule.operator == ">=" and not passed) else None
    unit = f" {rule.unit}" if rule.unit else ""
    explanation = f"'{rule.field_key}' expected {rule.operator} {expected:g}{unit}; observed {actual:g}{unit}."
    if gap is not None:
        explanation += f" Gap: {gap:g}{unit}."
    if rule.demo_only:
        explanation += " This is a DEMO-ONLY sample rule, not a verified official requirement."
    return {"status": "PASS" if passed else "FAIL", "expected": expected, "actual": actual,
            "gap": gap, "explanation": explanation}


def run_compliance_check(db: Session, application: Application, actor: User) -> list[ComplianceResult]:
    """Evaluate every active rule against the saved submitted_data; persist each result (Master Blueprint p.7)."""
    from app.services.alert_service import create_compliance_failure_alert

    rules = db.scalars(select(ComplianceRule).where(ComplianceRule.active.is_(True))
                       .order_by(ComplianceRule.code.asc())).all()
    results: list[ComplianceResult] = []
    for rule in rules:
        outcome = evaluate_rule(rule, application.submitted_data)
        result = ComplianceResult(
            application_id=application.id, rule_id=rule.id, rule_code=rule.code, rule_version=rule.version,
            field_key=rule.field_key, expected=outcome["expected"], actual=outcome["actual"],
            unit=rule.unit, status=outcome["status"], gap=outcome["gap"], explanation=outcome["explanation"],
            evidence_document_ids=[],
        )
        db.add(result)
        results.append(result)
        if outcome["status"] == "FAIL":
            create_compliance_failure_alert(db, application, rule, outcome)

    append_audit(db, actor_id=actor.id, action="COMPLIANCE_CHECK_RUN", entity_type="application",
                 entity_id=application.id,
                 details={"results": [{"rule_code": r.rule_code, "status": r.status} for r in results]})
    return results

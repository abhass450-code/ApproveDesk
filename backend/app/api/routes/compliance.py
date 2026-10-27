from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.application import Application
from app.models.compliance import ComplianceRule, ComplianceResult
from app.models.user import User
from app.schemas.common import UserRole
from app.schemas.compliance import (ComplianceCheckResponse, ComplianceResultOut, ComplianceRuleCreate,
                                    ComplianceRuleOut, ComplianceRuleUpdate)
from app.services.audit_service import append_audit
from app.services.compliance_service import ALLOWED_OPERATORS, run_compliance_check

router = APIRouter(tags=["Compliance"])


def _visible_application(db: Session, application_id: int, user: User) -> Application:
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role == UserRole.ADMIN.value:
        return app
    if user.role == UserRole.INSTITUTION.value and app.institution_id == user.institution_id:
        return app
    if user.role == UserRole.OFFICER.value and app.assigned_officer_id == user.id:
        return app
    raise HTTPException(status_code=404, detail="Application not found")


@router.get("/compliance/rules", response_model=list[ComplianceRuleOut])
def list_rules(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ComplianceRuleOut]:
    rules = db.scalars(select(ComplianceRule).order_by(ComplianceRule.code.asc())).all()
    return [ComplianceRuleOut.model_validate(rule) for rule in rules]


@router.post("/compliance/rules", response_model=ComplianceRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(payload: ComplianceRuleCreate, user: User = Depends(require_roles(UserRole.ADMIN)),
                db: Session = Depends(get_db)) -> ComplianceRuleOut:
    if payload.operator not in ALLOWED_OPERATORS:
        raise HTTPException(status_code=422, detail=f"Unsupported operator: {payload.operator}")
    if payload.operator != "exists" and payload.threshold_value is None:
        raise HTTPException(status_code=422, detail="threshold_value is required for comparison operators")
    existing = db.scalar(select(ComplianceRule).where(ComplianceRule.code == payload.code))
    if existing is not None:
        raise HTTPException(status_code=422, detail=f"Rule code already exists: {payload.code}")
    rule = ComplianceRule(**payload.model_dump())
    db.add(rule)
    append_audit(db, actor_id=user.id, action="COMPLIANCE_RULE_CREATED", entity_type="compliance_rule",
                 entity_id=None, details={"code": rule.code, "demo_only": rule.demo_only})
    db.commit()
    db.refresh(rule)
    return ComplianceRuleOut.model_validate(rule)


@router.patch("/compliance/rules/{rule_id}", response_model=ComplianceRuleOut)
def update_rule(rule_id: int, payload: ComplianceRuleUpdate, user: User = Depends(require_roles(UserRole.ADMIN)),
                db: Session = Depends(get_db)) -> ComplianceRuleOut:
    rule = db.get(ComplianceRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    changes = payload.model_dump(exclude_unset=True)
    material = {"field_key", "operator", "threshold_value"} & changes.keys()
    old_material = (rule.field_key, rule.operator, rule.threshold_value)
    for key, value in changes.items():
        setattr(rule, key, value)
    if material and (rule.field_key, rule.operator, rule.threshold_value) != old_material:
        rule.version += 1  # keep old results traceable to their rule version
    db.add(rule)
    append_audit(db, actor_id=user.id, action="COMPLIANCE_RULE_UPDATED", entity_type="compliance_rule",
                 entity_id=rule.id, details={"code": rule.code, "version": rule.version})
    db.commit()
    db.refresh(rule)
    return ComplianceRuleOut.model_validate(rule)


@router.post("/applications/{application_id}/compliance/check", response_model=ComplianceCheckResponse)
def check(application_id: int, user: User = Depends(require_roles(UserRole.OFFICER, UserRole.ADMIN)),
          db: Session = Depends(get_db)) -> ComplianceCheckResponse:
    application = _visible_application(db, application_id, user)
    results = run_compliance_check(db, application, user)
    db.commit()
    counts = {"PASS": 0, "FAIL": 0, "WARNING": 0, "NEEDS_REVIEW": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return ComplianceCheckResponse(
        application_id=application.id, evaluated_at=datetime.now(timezone.utc),
        summary={"total": len(results), "passed": counts["PASS"], "failed": counts["FAIL"],
                 "warnings": counts["WARNING"], "needs_review": counts["NEEDS_REVIEW"]},
        results=[ComplianceResultOut.model_validate(result) for result in results],
    )


@router.get("/applications/{application_id}/compliance/results", response_model=list[ComplianceResultOut])
def results(application_id: int, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)) -> list[ComplianceResultOut]:
    application = _visible_application(db, application_id, user)
    items = db.scalars(select(ComplianceResult).where(ComplianceResult.application_id == application.id)
                       .order_by(ComplianceResult.evaluated_at.desc(), ComplianceResult.id.desc())).all()
    return [ComplianceResultOut.model_validate(item) for item in items]

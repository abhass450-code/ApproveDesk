from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.application import Application
from app.models.compliance_result import ComplianceResult
from app.models.compliance_rule import ComplianceRule
from app.models.user import User
from app.schemas.common import UserRole
from app.schemas.compliance import (
    ComplianceEvaluateRequest,
    ComplianceResultResponse,
    ComplianceRuleCreate,
    ComplianceRuleResponse,
)
from app.services.compliance_service import evaluate_rule


router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post(
    "/rules",
    response_model=ComplianceRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    payload: ComplianceRuleCreate,
    user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ComplianceRuleResponse:
    existing = db.scalar(
        select(ComplianceRule).where(ComplianceRule.code == payload.code)
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A compliance rule with this code already exists",
        )

    rule = ComplianceRule(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        field_key=payload.field_key,
        operator=payload.operator,
        expected_value=payload.expected_value,
        severity=payload.severity,
        application_type=payload.application_type,
        programme=payload.programme,
        academic_year=payload.academic_year,
        source_title=payload.source_title,
        source_url=payload.source_url,
        source_clause=payload.source_clause,
        source_verified=payload.source_verified,
        is_active=True,
        version=1,
        created_by_id=user.id,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ComplianceRuleResponse.model_validate(rule)


@router.get(
    "/rules",
    response_model=list[ComplianceRuleResponse],
)
def list_rules(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ComplianceRuleResponse]:
    rules = db.scalars(
        select(ComplianceRule)
        .where(ComplianceRule.is_active.is_(True))
        .order_by(ComplianceRule.id.asc())
    ).all()

    return [
        ComplianceRuleResponse.model_validate(rule)
        for rule in rules
    ]


@router.post(
    "/evaluate",
    response_model=list[ComplianceResultResponse],
)
def evaluate_application(
    payload: ComplianceEvaluateRequest,
    user: User = Depends(
        require_roles(UserRole.OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
) -> list[ComplianceResultResponse]:
    application = db.get(Application, payload.application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if (
        user.role == UserRole.OFFICER.value
        and application.assigned_officer_id != user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    rules = db.scalars(
        select(ComplianceRule)
        .where(ComplianceRule.is_active.is_(True))
        .order_by(ComplianceRule.id.asc())
    ).all()

    if not rules:
        raise HTTPException(
            status_code=404,
            detail="No active compliance rules configured",
        )

    results = []

    for rule in rules:
        evaluation = evaluate_rule(rule, payload.values)

        result = ComplianceResult(
            application_id=application.id,
            rule_id=rule.id,
            rule_code=evaluation["rule_code"],
            rule_name=evaluation["rule_name"],
            rule_version=evaluation["rule_version"],
            field_key=evaluation["field_key"],
            operator=evaluation["operator"],
            expected_value=evaluation["expected_value"],
            actual_value=evaluation["actual_value"],
            status=evaluation["status"],
            severity=evaluation["severity"],
            gap_value=evaluation["gap_value"],
            explanation=evaluation["explanation"],
            source_title=evaluation["source_title"],
            source_url=evaluation["source_url"],
            source_clause=evaluation["source_clause"],
            source_verified=evaluation["source_verified"],
            evidence_document_ids=evaluation["evidence_document_ids"],
            evaluated_by_id=user.id,
        )

        db.add(result)
        results.append(result)

    db.commit()

    for result in results:
        db.refresh(result)

    return [
        ComplianceResultResponse.model_validate(result)
        for result in results
    ]


@router.get(
    "/applications/{application_id}/results",
    response_model=list[ComplianceResultResponse],
)
def get_application_results(
    application_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ComplianceResultResponse]:
    application = db.get(Application, application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if user.role == UserRole.INSTITUTION.value:
        if application.institution_id != user.institution_id:
            raise HTTPException(
                status_code=404,
                detail="Application not found",
            )

    elif user.role == UserRole.OFFICER.value:
        if application.assigned_officer_id != user.id:
            raise HTTPException(
                status_code=404,
                detail="Application not found",
            )

    elif user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Insufficient role",
        )

    results = db.scalars(
        select(ComplianceResult)
        .where(ComplianceResult.application_id == application.id)
        .order_by(
            ComplianceResult.evaluated_at.desc(),
            ComplianceResult.id.desc(),
        )
    ).all()

    return [
        ComplianceResultResponse.model_validate(result)
        for result in results
    ]

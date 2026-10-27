from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import ApplicationStatus


class ApplicationCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    description: str | None = Field(default=None, max_length=10000)
    submitted_data: dict[str, Any] | None = Field(default=None, max_length=100)
    due_at: datetime | None = None


class ApplicationDataUpdate(BaseModel):
    submitted_data: dict[str, Any] = Field(min_length=1)


class ApplicationOut(BaseModel):
    id: int
    application_code: str
    institution_id: int
    created_by_id: int
    assigned_officer_id: int | None
    title: str
    description: str | None
    current_stage: ApplicationStatus
    correction_return_stage: ApplicationStatus | None
    submitted_data: dict[str, Any] | None
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentOut(BaseModel):
    id: int
    application_id: int
    filename: str
    content_type: str | None
    verified: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransitionRequest(BaseModel):
    to_stage: ApplicationStatus
    note: str | None = Field(default=None, max_length=2000)


class AssignmentRequest(BaseModel):
    assigned_officer_id: int = Field(gt=0)


class StageHistoryOut(BaseModel):
    id: int
    application_id: int
    from_stage: str | None
    to_stage: str
    changed_by_id: int | None
    note: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: dict | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ApplicationHistoryOut(BaseModel):
    application_id: int
    stages: list[StageHistoryOut]
    audit_events: list[AuditLogOut]

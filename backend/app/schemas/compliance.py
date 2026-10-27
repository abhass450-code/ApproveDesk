from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

Operator = Literal[">=", "<=", "==", "!=", "exists"]
Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class ComplianceRuleCreate(BaseModel):
    code: str = Field(min_length=3, max_length=60)
    name: str = Field(min_length=3, max_length=200)
    category: str = Field(default="GENERAL", max_length=60)
    field_key: str = Field(min_length=1, max_length=120)
    operator: Operator
    threshold_value: Any | None = None
    unit: str | None = Field(default=None, max_length=40)
    severity: Severity = "MEDIUM"
    demo_only: bool = True
    source_title: str | None = Field(default=None, max_length=240)
    source_url: str | None = Field(default=None, max_length=500)
    source_clause: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=5000)


class ComplianceRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=200)
    field_key: str | None = Field(default=None, min_length=1, max_length=120)
    operator: Operator | None = None
    threshold_value: Any | None = None
    unit: str | None = Field(default=None, max_length=40)
    severity: Severity | None = None
    active: bool | None = None
    demo_only: bool | None = None
    description: str | None = Field(default=None, max_length=5000)


class ComplianceRuleOut(BaseModel):
    id: int
    code: str
    name: str
    category: str
    field_key: str
    operator: str
    threshold_value: Any | None
    unit: str | None
    severity: str
    active: bool
    version: int
    demo_only: bool
    source_title: str | None
    source_url: str | None
    source_clause: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ComplianceResultOut(BaseModel):
    id: int
    application_id: int
    rule_id: int | None
    rule_code: str
    rule_version: int
    field_key: str
    expected: Any | None
    actual: Any | None
    unit: str | None
    status: str
    gap: float | None
    explanation: str | None
    evidence_document_ids: list[int] | None
    evaluated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ComplianceCheckResponse(BaseModel):
    application_id: int
    evaluated_at: datetime
    summary: dict[str, int]
    results: list[ComplianceResultOut]

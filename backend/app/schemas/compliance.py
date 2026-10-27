from typing import Any

from pydantic import BaseModel, Field


class ComplianceRuleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=2, max_length=180)
    description: str | None = None

    category: str
    field_key: str
    operator: str
    expected_value: Any = None

    severity: str = "MEDIUM"

    application_type: str | None = None
    programme: str | None = None
    academic_year: str | None = None

    source_title: str | None = None
    source_url: str | None = None
    source_clause: str | None = None
    source_verified: bool = False


class ComplianceRuleResponse(ComplianceRuleCreate):
    id: int
    version: int
    is_active: bool

    model_config = {"from_attributes": True}


class ComplianceEvaluateRequest(BaseModel):
    application_id: int
    values: dict[str, Any] = Field(default_factory=dict)


class ComplianceResultResponse(BaseModel):
    id: int
    application_id: int
    rule_id: int

    rule_code: str
    rule_name: str
    rule_version: int

    field_key: str
    operator: str
    expected_value: Any = None
    actual_value: Any = None

    status: str
    severity: str
    gap_value: float | None = None
    explanation: str

    source_title: str | None = None
    source_url: str | None = None
    source_clause: str | None = None
    source_verified: bool

    evidence_document_ids: list[int]

    model_config = {"from_attributes": True}

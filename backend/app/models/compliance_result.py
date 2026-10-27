from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    __table_args__ = (
        Index(
            "ix_compliance_results_application_evaluated",
            "application_id",
            "evaluated_at",
        ),
        Index(
            "ix_compliance_results_application_status",
            "application_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("compliance_rules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Snapshot of the rule used for this evaluation.
    rule_code: Mapped[str] = mapped_column(String(60), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(180), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)

    field_key: Mapped[str] = mapped_column(String(120), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    expected_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    actual_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(24), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    gap_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # Store source details as they were at evaluation time.
    source_title: Mapped[str | None] = mapped_column(
        String(240), nullable=True
    )
    source_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )
    source_clause: Mapped[str | None] = mapped_column(
        String(160), nullable=True
    )
    source_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    evidence_document_ids: Mapped[list[int]] = mapped_column(
        JSON, default=list, nullable=False
    )

    evaluated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

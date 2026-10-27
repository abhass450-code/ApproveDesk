from datetime import datetime, timezone
from typing import Any
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"
    __table_args__ = (Index("ix_compliance_rules_code", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="GENERAL", nullable=False)
    field_key: Mapped[str] = mapped_column(String(120), nullable=False)
    operator: Mapped[str] = mapped_column(String(8), nullable=False)
    threshold_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    demo_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_title: Mapped[str | None] = mapped_column(String(240), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_clause: Mapped[str | None] = mapped_column(String(240), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    __table_args__ = (
        Index("ix_compliance_results_application_id", "application_id"),
        Index("ix_compliance_results_rule_id", "rule_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("compliance_rules.id", ondelete="SET NULL"), nullable=True)
    rule_code: Mapped[str] = mapped_column(String(60), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    field_key: Mapped[str] = mapped_column(String(120), nullable=False)
    expected: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    actual: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    gap: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_document_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

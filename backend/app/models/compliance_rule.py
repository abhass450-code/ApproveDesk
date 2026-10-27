from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"
    __table_args__ = (
        Index("ix_compliance_rules_active", "is_active"),
        Index(
            "ix_compliance_rules_applicability",
            "application_type",
            "programme",
            "academic_year",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(
        String(60), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[str] = mapped_column(String(80), nullable=False)
    field_key: Mapped[str] = mapped_column(String(120), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    expected_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    severity: Mapped[str] = mapped_column(
        String(20), default="MEDIUM", nullable=False
    )

    application_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    programme: Mapped[str | None] = mapped_column(
        String(160), nullable=True
    )
    academic_year: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

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

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_applications_institution_id", "institution_id"),
        Index("ix_applications_assigned_officer_id", "assigned_officer_id"),
        Index("ix_applications_current_stage", "current_stage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigned_officer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_stage: Mapped[str] = mapped_column(String(32), default="SUBMITTED", nullable=False)
    correction_return_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    submitted_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

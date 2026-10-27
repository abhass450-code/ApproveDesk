import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AlertType(str, enum.Enum):
    DEADLINE_SOON = "DEADLINE_SOON"
    OVERDUE_STAGE = "OVERDUE_STAGE"
    COMPLIANCE_FAILURE = "COMPLIANCE_FAILURE"
    DOCUMENT_EXPIRING = "DOCUMENT_EXPIRING"
    QUERY_RESPONSE_OVERDUE = "QUERY_RESPONSE_OVERDUE"

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String, nullable=False, index=True)
    recipient_id = Column(String, nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    message = Column(String, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN, nullable=False)
    dedupe_key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_alert_recipient_status", "recipient_id", "status"),
        Index("idx_alert_due_at", "due_at"),
    )
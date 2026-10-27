from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.alert import AlertType, AlertSeverity, AlertStatus

class AlertBase(BaseModel):
    application_id: str
    recipient_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    due_at: Optional[datetime] = None

class AlertCreate(AlertBase):
    dedupe_key: str

class AlertRead(AlertBase):
    id: str
    status: AlertStatus
    dedupe_key: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AlertAcknowledge(BaseModel):
    acknowledged_at: Optional[datetime] = None

class ScanResult(BaseModel):
    created_count: int
    updated_count: int
    skipped_count: int
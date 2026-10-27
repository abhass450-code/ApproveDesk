from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    id: int
    application_id: int
    recipient_id: int | None
    alert_type: str
    severity: str
    message: str
    due_at: datetime | None
    status: str
    dedupe_key: str
    created_at: datetime
    acknowledged_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class ScanResultOut(BaseModel):
    created: int
    skipped: int

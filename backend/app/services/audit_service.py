from typing import Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def append_audit(db: Session, *, actor_id: int | None, action: str, entity_type: str,
                 entity_id: int | None, details: dict[str, Any] | None = None) -> AuditLog:
    entry = AuditLog(actor_id=actor_id, action=action, entity_type=entity_type,
                     entity_id=entity_id, details=details)
    db.add(entry)
    return entry

"""
Audit logging service
"""
from typing import Any, Optional
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from models.audit import AuditLog


def _normalize_payload(payload: Any) -> Optional[dict]:
    if payload is None:
        return None
    return jsonable_encoder(payload)


def log_audit(
    db: Session,
    user_id: Optional[int],
    user_email: Optional[str],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    before: Any = None,
    after: Any = None,
    ip_address: Optional[str] = None
) -> Optional[AuditLog]:
    """Create an audit log entry"""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            before_data=_normalize_payload(before),
            after_data=_normalize_payload(after),
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception:
        db.rollback()
        return None

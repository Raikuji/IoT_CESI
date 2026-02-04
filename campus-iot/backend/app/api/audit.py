"""
Audit Log API - Tracks who changed what and when
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from db.database import get_db
from models.audit import AuditLog
from models.user import User
from api.auth import require_permission

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[str]
    before_data: Optional[dict]
    after_data: Optional[dict]
    user_id: Optional[int]
    user_email: Optional[str]
    ip_address: Optional[str]
    timestamp: str

    class Config:
        from_attributes = True


def audit_to_response(log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=log.id,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        before_data=log.before_data,
        after_data=log.after_data,
        user_id=log.user_id,
        user_email=log.user_email,
        ip_address=log.ip_address,
        timestamp=log.created_at.isoformat() if log.created_at else datetime.utcnow().isoformat()
    )


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(require_permission("audit")),
    db: Session = Depends(get_db)
):
    """Get audit logs with filters (admin/audit permission)"""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == str(entity_id))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
    return [audit_to_response(l) for l in logs]

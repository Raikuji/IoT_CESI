"""
Activity Log API - Connected to Supabase
Tracks all user actions in the system
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from db.database import get_db
from models.user import ActivityLog, User
from api.auth import get_current_user
from services.websocket_manager import ws_manager

router = APIRouter(prefix="/activity", tags=["Activity"])

# Action type definitions
ACTION_TYPES = {
    "login": {"label": "Connexion", "icon": "mdi-login", "color": "#22c55e"},
    "logout": {"label": "Déconnexion", "icon": "mdi-logout", "color": "#64748b"},
    "register": {"label": "Inscription", "icon": "mdi-account-plus", "color": "#22c55e"},
    "sensor_add": {"label": "Capteur ajouté", "icon": "mdi-plus-circle", "color": "#3b82f6"},
    "sensor_remove": {"label": "Capteur retiré", "icon": "mdi-minus-circle", "color": "#ef4444"},
    "sensor_assign": {"label": "Capteur assigné", "icon": "mdi-map-marker-plus", "color": "#8b5cf6"},
    "alert_triggered": {"label": "Alerte déclenchée", "icon": "mdi-bell-alert", "color": "#f59e0b"},
    "alert_resolved": {"label": "Alerte résolue", "icon": "mdi-bell-check", "color": "#22c55e"},
    "command_sent": {"label": "Commande envoyée", "icon": "mdi-send", "color": "#8b5cf6"},
    "heating_changed": {"label": "Chauffage modifié", "icon": "mdi-radiator", "color": "#ef4444"},
    "user_created": {"label": "Utilisateur créé", "icon": "mdi-account-plus", "color": "#22c55e"},
    "user_updated": {"label": "Utilisateur modifié", "icon": "mdi-account-edit", "color": "#3b82f6"},
    "user_deleted": {"label": "Utilisateur supprimé", "icon": "mdi-account-remove", "color": "#ef4444"},
    "role_changed": {"label": "Rôle modifié", "icon": "mdi-shield-edit", "color": "#f59e0b"},
    "settings_changed": {"label": "Paramètres modifiés", "icon": "mdi-cog", "color": "#64748b"},
    "export_data": {"label": "Export données", "icon": "mdi-download", "color": "#06b6d4"},
    "report_issue": {"label": "Problème signalé", "icon": "mdi-alert-circle", "color": "#ef4444"},
}


class ActivityLogCreate(BaseModel):
    action: str
    details: Optional[str] = None


class ActivityLogResponse(BaseModel):
    id: int
    action: str
    label: str
    icon: str
    color: str
    details: Optional[str]
    user_id: Optional[int]
    user_name: str
    user_email: Optional[str]
    ip_address: Optional[str]
    timestamp: str

    class Config:
        from_attributes = True


def log_to_response(log: ActivityLog, db: Session) -> ActivityLogResponse:
    """Convert ActivityLog model to response"""
    action_info = ACTION_TYPES.get(log.action, {
        "label": log.action,
        "icon": "mdi-information",
        "color": "#64748b"
    })
    
    # Get user name
    user_name = "Système"
    if log.user_id:
        user = db.query(User).filter(User.id == log.user_id).first()
        if user:
            user_name = f"{user.first_name} {user.last_name}"
    elif log.user_email:
        user_name = log.user_email.split('@')[0]
    
    return ActivityLogResponse(
        id=log.id,
        action=log.action,
        label=action_info["label"],
        icon=action_info["icon"],
        color=action_info["color"],
        details=log.details,
        user_id=log.user_id,
        user_name=user_name,
        user_email=log.user_email,
        ip_address=log.ip_address,
        timestamp=log.created_at.isoformat() if log.created_at else datetime.utcnow().isoformat()
    )


async def add_activity_log(
    db: Session,
    action: str,
    user_id: int = None,
    user_email: str = None,
    details: str = None,
    ip_address: str = None
) -> ActivityLog:
    """Add an activity log entry to the database"""
    log_entry = ActivityLog(
        action=action,
        user_id=user_id,
        user_email=user_email,
        details=details,
        ip_address=ip_address
    )
    
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    # Broadcast to all connected clients
    action_info = ACTION_TYPES.get(action, {"label": action, "icon": "mdi-information", "color": "#64748b"})
    
    await ws_manager.broadcast({
        "type": "activity_log",
        "log": {
            "id": log_entry.id,
            "action": action,
            "label": action_info["label"],
            "icon": action_info["icon"],
            "color": action_info["color"],
            "details": details,
            "user_id": user_id,
            "user_email": user_email,
            "timestamp": log_entry.created_at.isoformat() if log_entry.created_at else datetime.utcnow().isoformat()
        }
    })
    
    return log_entry


@router.post("/log", response_model=ActivityLogResponse)
async def create_log(
    log_data: ActivityLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new activity log entry"""
    log_entry = await add_activity_log(
        db=db,
        action=log_data.action,
        user_id=current_user.id,
        user_email=current_user.email,
        details=log_data.details
    )
    return log_to_response(log_entry, db)


@router.get("/logs", response_model=List[ActivityLogResponse])
async def get_logs(
    limit: int = Query(default=100, le=500),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity logs from database"""
    query = db.query(ActivityLog)
    
    # Filter by action if specified
    if action:
        query = query.filter(ActivityLog.action == action)
    
    # Filter by user if specified
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    # Order by most recent first
    logs = query.order_by(desc(ActivityLog.created_at)).limit(limit).all()
    
    return [log_to_response(log, db) for log in logs]


@router.get("/logs/user/{user_id}", response_model=List[ActivityLogResponse])
async def get_user_logs(
    user_id: int,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity logs for a specific user"""
    logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id
    ).order_by(desc(ActivityLog.created_at)).limit(limit).all()
    
    return [log_to_response(log, db) for log in logs]


@router.get("/types")
async def get_action_types():
    """Get all action types"""
    return ACTION_TYPES


@router.get("/stats")
async def get_activity_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity statistics"""
    from sqlalchemy import func
    
    # Count by action type
    stats = db.query(
        ActivityLog.action,
        func.count(ActivityLog.id).label('count')
    ).group_by(ActivityLog.action).all()
    
    result = {s.action: s.count for s in stats}
    result['total'] = sum(result.values())
    
    return result

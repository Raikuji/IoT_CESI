from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .auth import get_current_user

router = APIRouter(prefix="/activity", tags=["Activity"])

# In-memory activity log storage
activity_logs = []
log_id_counter = 0

# Action type definitions
ACTION_TYPES = {
    "login": {"label": "Connexion", "icon": "mdi-login", "color": "#22c55e"},
    "logout": {"label": "Déconnexion", "icon": "mdi-logout", "color": "#64748b"},
    "sensor_add": {"label": "Capteur ajouté", "icon": "mdi-plus-circle", "color": "#3b82f6"},
    "sensor_remove": {"label": "Capteur retiré", "icon": "mdi-minus-circle", "color": "#ef4444"},
    "alert_triggered": {"label": "Alerte déclenchée", "icon": "mdi-bell-alert", "color": "#f59e0b"},
    "alert_resolved": {"label": "Alerte résolue", "icon": "mdi-bell-check", "color": "#22c55e"},
    "command_sent": {"label": "Commande envoyée", "icon": "mdi-send", "color": "#8b5cf6"},
    "user_created": {"label": "Utilisateur créé", "icon": "mdi-account-plus", "color": "#22c55e"},
    "user_updated": {"label": "Utilisateur modifié", "icon": "mdi-account-edit", "color": "#3b82f6"},
    "user_deleted": {"label": "Utilisateur supprimé", "icon": "mdi-account-remove", "color": "#ef4444"},
    "role_changed": {"label": "Rôle modifié", "icon": "mdi-shield-edit", "color": "#f59e0b"},
    "settings_changed": {"label": "Paramètres modifiés", "icon": "mdi-cog", "color": "#64748b"},
    "export_data": {"label": "Export données", "icon": "mdi-download", "color": "#06b6d4"},
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
    user_id: int
    user_name: str
    timestamp: str


def add_activity_log(action: str, user_id: int, user_name: str, details: str = None):
    """Add an activity log entry"""
    global log_id_counter
    log_id_counter += 1
    
    action_info = ACTION_TYPES.get(action, {
        "label": action,
        "icon": "mdi-information",
        "color": "#64748b"
    })
    
    log_entry = {
        "id": log_id_counter,
        "action": action,
        "label": action_info["label"],
        "icon": action_info["icon"],
        "color": action_info["color"],
        "details": details,
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    activity_logs.insert(0, log_entry)
    
    # Keep only last 500 logs
    if len(activity_logs) > 500:
        activity_logs.pop()
    
    return log_entry


@router.post("/log", response_model=ActivityLogResponse)
async def create_log(
    log_data: ActivityLogCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new activity log entry"""
    log_entry = add_activity_log(
        action=log_data.action,
        user_id=current_user["id"],
        user_name=f"{current_user['first_name']} {current_user['last_name']}",
        details=log_data.details
    )
    return log_entry


@router.get("/logs", response_model=List[ActivityLogResponse])
async def get_logs(
    limit: int = 50,
    action: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get activity logs"""
    logs = activity_logs
    
    # Filter by action if specified
    if action:
        logs = [l for l in logs if l["action"] == action]
    
    return logs[:limit]


@router.get("/logs/user/{user_id}", response_model=List[ActivityLogResponse])
async def get_user_logs(
    user_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get activity logs for a specific user"""
    logs = [l for l in activity_logs if l["user_id"] == user_id]
    return logs[:limit]


@router.get("/types")
async def get_action_types():
    """Get all action types"""
    return ACTION_TYPES

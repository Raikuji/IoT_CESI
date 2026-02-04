"""
System Settings & User Preferences API
Synced to Supabase for all users
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from db.database import get_db
from models.settings import SystemSetting, UserPreference
from models.user import User
from api.auth import get_current_user, get_current_admin, get_control_user
from services.websocket_manager import ws_manager
from services.audit_service import log_audit

router = APIRouter(prefix="/settings", tags=["Settings"])


# =============================================
# SYSTEM SETTINGS
# =============================================

class SettingUpdate(BaseModel):
    value: str


class SettingResponse(BaseModel):
    id: int
    key: str
    value: Optional[str]
    value_type: str
    category: str
    description: Optional[str]
    updated_at: str

    class Config:
        from_attributes = True


def setting_to_response(setting: SystemSetting) -> SettingResponse:
    return SettingResponse(
        id=setting.id,
        key=setting.key,
        value=setting.value,
        value_type=setting.value_type or "string",
        category=setting.category or "general",
        description=setting.description,
        updated_at=setting.updated_at.isoformat() if setting.updated_at else datetime.utcnow().isoformat()
    )


def setting_snapshot(setting: SystemSetting) -> dict:
    return {
        "id": setting.id,
        "key": setting.key,
        "value": setting.value,
        "value_type": setting.value_type,
        "category": setting.category,
        "description": setting.description,
        "updated_by_user_id": setting.updated_by_user_id,
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
    }


def parse_setting_value(value: str, value_type: str):
    """Parse setting value based on its type"""
    if value_type == "number":
        try:
            return float(value) if "." in value else int(value)
        except:
            return value
    elif value_type == "boolean":
        return value.lower() in ("true", "1", "yes", "on")
    elif value_type == "json":
        import json
        try:
            return json.loads(value)
        except:
            return value
    return value


@router.get("/", response_model=List[SettingResponse])
@router.get("/system", response_model=List[SettingResponse])
async def get_all_settings(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all system settings"""
    query = db.query(SystemSetting)
    if category:
        query = query.filter(SystemSetting.category == category)
    settings = query.order_by(SystemSetting.category, SystemSetting.key).all()
    return [setting_to_response(s) for s in settings]


@router.get("/system/dict")
async def get_settings_as_dict(db: Session = Depends(get_db)):
    """Get all settings as a dictionary with parsed values"""
    settings = db.query(SystemSetting).all()
    result = {}
    for s in settings:
        result[s.key] = parse_setting_value(s.value, s.value_type)
    return result


@router.get("/system/{key}")
async def get_setting(key: str, db: Session = Depends(get_db)):
    """Get a specific setting by key"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {
        "key": setting.key,
        "value": parse_setting_value(setting.value, setting.value_type),
        "raw_value": setting.value,
        "type": setting.value_type,
        "category": setting.category,
        "description": setting.description
    }


@router.put("/system/{key}")
async def update_setting(
    key: str,
    data: SettingUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update a system setting (admin only)"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    before = setting_snapshot(setting)
    setting.value = data.value
    setting.updated_by_user_id = current_user.id
    setting.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(setting)
    
    # Broadcast setting change to all clients
    await ws_manager.broadcast({
        "type": "system_setting_updated",
        "key": key,
        "value": parse_setting_value(setting.value, setting.value_type)
    })

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="update",
        entity_type="system_setting",
        entity_id=setting.id,
        before=before,
        after=setting_snapshot(setting),
        ip_address=request.client.host if request and request.client else None
    )
    
    return setting_to_response(setting)


# Heating-specific endpoints (accessible to all authenticated users)
HEATING_KEYS = ["heating_mode", "heating_value", "heating_setpoint"]

@router.put("/{key}")
async def update_heating_setting(
    key: str,
    data: SettingUpdate,
    current_user: User = Depends(get_control_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update heating settings (requires control permission: admin, technician, manager)"""
    if key not in HEATING_KEYS:
        raise HTTPException(status_code=403, detail="Only heating settings can be updated here")
    
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    
    # Create if not exists
    if not setting:
        before = None
        setting = SystemSetting(
            key=key,
            value=data.value,
            value_type="number" if key in ["heating_value", "heating_setpoint"] else "string",
            category="heating",
            description=f"Heating {key.replace('heating_', '')}",
            updated_by_user_id=current_user.id
        )
        db.add(setting)
    else:
        before = setting_snapshot(setting)
        setting.value = data.value
        setting.updated_by_user_id = current_user.id
        setting.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(setting)
    
    # Broadcast setting change to all clients
    await ws_manager.broadcast({
        "type": "system_setting_updated",
        "key": key,
        "value": parse_setting_value(setting.value, setting.value_type)
    })

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="update" if before else "create",
        entity_type="system_setting",
        entity_id=setting.id,
        before=before,
        after=setting_snapshot(setting),
        ip_address=request.client.host if request and request.client else None
    )
    
    return setting_to_response(setting)


@router.put("/system/bulk")
async def update_settings_bulk(
    settings: Dict[str, str],
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update multiple settings at once (admin only)"""
    updated = []
    for key, value in settings.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            before = setting_snapshot(setting)
            setting.value = value
            setting.updated_by_user_id = current_user.id
            setting.updated_at = datetime.utcnow()
            updated.append(key)

            log_audit(
                db=db,
                user_id=current_user.id,
                user_email=current_user.email,
                action="update",
                entity_type="system_setting",
                entity_id=setting.id,
                before=before,
                after=setting_snapshot(setting),
                ip_address=request.client.host if request and request.client else None
            )
    
    db.commit()
    
    # Broadcast
    await ws_manager.broadcast({
        "type": "settings_bulk_changed",
        "keys": updated
    })
    
    return {"success": True, "updated": updated}


# =============================================
# USER PREFERENCES
# =============================================

class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    default_floor: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_alerts: Optional[bool] = None
    sound_alerts: Optional[bool] = None
    dashboard_layout: Optional[Dict[str, Any]] = None
    favorite_rooms: Optional[List[str]] = None


class PreferencesResponse(BaseModel):
    user_id: int
    theme: str
    default_floor: str
    notifications_enabled: bool
    email_alerts: bool
    sound_alerts: bool
    dashboard_layout: Dict[str, Any]
    favorite_rooms: List[str]
    updated_at: str

    class Config:
        from_attributes = True


def prefs_to_response(prefs: UserPreference) -> PreferencesResponse:
    return PreferencesResponse(
        user_id=prefs.user_id,
        theme=prefs.theme or "dark",
        default_floor=prefs.default_floor or "RDC",
        notifications_enabled=prefs.notifications_enabled if prefs.notifications_enabled is not None else True,
        email_alerts=prefs.email_alerts if prefs.email_alerts is not None else False,
        sound_alerts=prefs.sound_alerts if prefs.sound_alerts is not None else True,
        dashboard_layout=prefs.dashboard_layout or {},
        favorite_rooms=prefs.favorite_rooms or [],
        updated_at=prefs.updated_at.isoformat() if prefs.updated_at else datetime.utcnow().isoformat()
    )


@router.get("/preferences", response_model=PreferencesResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's preferences"""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    # Create default preferences if not exist
    if not prefs:
        prefs = UserPreference(
            user_id=current_user.id,
            theme="dark",
            default_floor="RDC",
            notifications_enabled=True,
            email_alerts=False,
            sound_alerts=True,
            dashboard_layout={},
            favorite_rooms=[]
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs_to_response(prefs)


@router.put("/preferences", response_model=PreferencesResponse)
async def update_my_preferences(
    data: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's preferences"""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
    
    if data.theme is not None:
        prefs.theme = data.theme
    if data.default_floor is not None:
        prefs.default_floor = data.default_floor
    if data.notifications_enabled is not None:
        prefs.notifications_enabled = data.notifications_enabled
    if data.email_alerts is not None:
        prefs.email_alerts = data.email_alerts
    if data.sound_alerts is not None:
        prefs.sound_alerts = data.sound_alerts
    if data.dashboard_layout is not None:
        prefs.dashboard_layout = data.dashboard_layout
    if data.favorite_rooms is not None:
        prefs.favorite_rooms = data.favorite_rooms
    
    prefs.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(prefs)
    
    return prefs_to_response(prefs)


@router.post("/preferences/favorite-room/{room_id}")
async def add_favorite_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a room to favorites"""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not prefs:
        prefs = UserPreference(user_id=current_user.id, favorite_rooms=[room_id])
        db.add(prefs)
    else:
        favorites = prefs.favorite_rooms or []
        if room_id not in favorites:
            favorites.append(room_id)
            prefs.favorite_rooms = favorites
    
    db.commit()
    return {"success": True, "favorites": prefs.favorite_rooms}


@router.delete("/preferences/favorite-room/{room_id}")
async def remove_favorite_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a room from favorites"""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if prefs and prefs.favorite_rooms:
        favorites = [r for r in prefs.favorite_rooms if r != room_id]
        prefs.favorite_rooms = favorites
        db.commit()
    
    return {"success": True, "favorites": prefs.favorite_rooms if prefs else []}

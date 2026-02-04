"""
Alerts API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from db import get_db
from models import Alert, AlertRule, Sensor
from schemas import (
    AlertCreate, AlertResponse,
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse
)
from api.auth import require_permission, require_any_permission
from services.audit_service import log_audit
from services.websocket_manager import ws_manager

router = APIRouter(prefix="/alerts", tags=["alerts"])


def alert_rule_snapshot(rule: AlertRule) -> dict:
    return {
        "id": rule.id,
        "sensor_id": rule.sensor_id,
        "condition": rule.condition,
        "threshold": rule.threshold,
        "message": rule.message,
        "severity": rule.severity,
        "name": rule.name,
        "sensor_type": rule.sensor_type,
        "room_id": rule.room_id,
        "active_days": rule.active_days,
        "active_time_start": rule.active_time_start,
        "active_time_end": rule.active_time_end,
        "cooldown_minutes": rule.cooldown_minutes,
        "escalation_minutes": rule.escalation_minutes,
        "escalation_severity": rule.escalation_severity,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None
    }


def alert_snapshot(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "sensor_id": alert.sensor_id,
        "type": alert.type,
        "message": alert.message,
        "severity": alert.severity,
        "is_acknowledged": alert.is_acknowledged,
        "rule_id": alert.rule_id,
        "escalation_level": alert.escalation_level,
        "escalated_from_alert_id": alert.escalated_from_alert_id,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
    }


def _validate_time(value: Optional[str]) -> bool:
    if not value:
        return True
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        return False


def _validate_rule_payload(data: dict, creating: bool = True):
    valid_conditions = ['>', '<', '>=', '<=', '==', '!=']
    valid_severities = ['info', 'warning', 'danger']

    if creating:
        if data.get('sensor_id') is None and not data.get('sensor_type'):
            raise HTTPException(
                status_code=400,
                detail="Une règle doit cibler un capteur ou un type de capteur"
            )

    if data.get('room_id') and not (data.get('sensor_id') or data.get('sensor_type')):
        raise HTTPException(
            status_code=400,
            detail="Le filtrage par salle nécessite un capteur ou un type"
        )

    if 'condition' in data and data['condition'] not in valid_conditions:
        raise HTTPException(
            status_code=400,
            detail=f"Condition invalide. Valeurs: {valid_conditions}"
        )

    if 'severity' in data and data['severity'] and data['severity'] not in valid_severities:
        raise HTTPException(
            status_code=400,
            detail=f"Sévérité invalide. Valeurs: {valid_severities}"
        )

    if 'escalation_severity' in data and data['escalation_severity'] and data['escalation_severity'] not in valid_severities:
        raise HTTPException(
            status_code=400,
            detail=f"Sévérité d'escalade invalide. Valeurs: {valid_severities}"
        )

    if (data.get('active_time_start') and not data.get('active_time_end')) or (data.get('active_time_end') and not data.get('active_time_start')):
        raise HTTPException(
            status_code=400,
            detail="La plage horaire doit contenir un début et une fin"
        )

    if not _validate_time(data.get('active_time_start')) or not _validate_time(data.get('active_time_end')):
        raise HTTPException(
            status_code=400,
            detail="Format horaire invalide (HH:MM)"
        )

    if data.get('active_days') is not None:
        days = data['active_days']
        if not isinstance(days, list) or any((d < 0 or d > 6) for d in days):
            raise HTTPException(
                status_code=400,
                detail="active_days doit être une liste d'entiers entre 0 et 6"
            )

    if data.get('cooldown_minutes') is not None and data['cooldown_minutes'] < 0:
        raise HTTPException(
            status_code=400,
            detail="cooldown_minutes doit être positif"
        )

    if data.get('escalation_minutes') is not None and data['escalation_minutes'] < 1:
        raise HTTPException(
            status_code=400,
            detail="escalation_minutes doit être >= 1"
        )

    if data.get('escalation_minutes') and not data.get('escalation_severity'):
        raise HTTPException(
            status_code=400,
            detail="escalation_severity requis si escalation_minutes est défini"
        )


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
    acknowledged: Optional[bool] = None,
    severity: Optional[str] = None,
    sensor_id: Optional[int] = None,
    current_user=Depends(require_any_permission(["alerts", "dashboard"])),
    db: Session = Depends(get_db)
):
    """Get all alerts with optional filters"""
    query = db.query(Alert)
    
    if acknowledged is not None:
        query = query.filter(Alert.is_acknowledged == acknowledged)
    if severity:
        query = query.filter(Alert.severity == severity)
    if sensor_id:
        query = query.filter(Alert.sensor_id == sensor_id)
    
    alerts = query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
    return alerts


@router.get("/active", response_model=List[AlertResponse])
def get_active_alerts(
    current_user=Depends(require_any_permission(["alerts", "dashboard"])),
    db: Session = Depends(get_db)
):
    """Get all unacknowledged alerts"""
    alerts = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).order_by(desc(Alert.created_at)).all()
    return alerts


@router.post("/{alert_id}/ack", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: int,
    current_user=Depends(require_permission("alerts")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    before = alert_snapshot(alert)
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="acknowledge",
        entity_type="alert",
        entity_id=alert.id,
        before=before,
        after=alert_snapshot(alert),
        ip_address=request.client.host if request and request.client else None
    )
    return alert


@router.post("/ack-all")
def acknowledge_all_alerts(
    current_user=Depends(require_permission("alerts")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Acknowledge all active alerts"""
    now = datetime.utcnow()
    alerts = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).all()

    result = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).update({
        "is_acknowledged": True,
        "acknowledged_at": now
    })
    db.commit()

    for alert in alerts:
        log_audit(
            db=db,
            user_id=current_user.id,
            user_email=current_user.email,
            action="acknowledge",
            entity_type="alert",
            entity_id=alert.id,
            before=alert_snapshot(alert),
            after={"is_acknowledged": True, "acknowledged_at": now.isoformat()},
            ip_address=request.client.host if request and request.client else None
        )
    return {"acknowledged": result}


# Alert Rules
@router.get("/rules", response_model=List[AlertRuleResponse])
def get_alert_rules(
    active_only: bool = True,
    current_user=Depends(require_permission("alerts")),
    db: Session = Depends(get_db)
):
    """Get all alert rules"""
    query = db.query(AlertRule)
    if active_only:
        query = query.filter(AlertRule.is_active == True)
    rules = query.all()
    return rules


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user=Depends(require_permission("alerts")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a new alert rule"""
    payload = rule.model_dump()
    _validate_rule_payload(payload, creating=True)

    # Verify sensor exists if sensor_id provided
    if rule.sensor_id is not None:
        sensor = db.query(Sensor).filter(Sensor.id == rule.sensor_id).first()
        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
    
    db_rule = AlertRule(**payload)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    # Broadcast to all clients
    await ws_manager.broadcast({
        "type": "alert_rules_changed",
        "action": "create",
        "rule": alert_rule_snapshot(db_rule)
    })

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="create",
        entity_type="alert_rule",
        entity_id=db_rule.id,
        before=None,
        after=alert_rule_snapshot(db_rule),
        ip_address=request.client.host if request and request.client else None
    )
    return db_rule


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule: AlertRuleUpdate,
    current_user=Depends(require_permission("alerts")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update an alert rule"""
    db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    before = alert_rule_snapshot(db_rule)
    update_data = rule.model_dump(exclude_unset=True)

    if update_data:
        merged = alert_rule_snapshot(db_rule)
        merged.update(update_data)
        _validate_rule_payload(merged, creating=False)
    
    # Verify sensor exists if sensor_id is updated
    if 'sensor_id' in update_data and update_data['sensor_id'] is not None:
        sensor = db.query(Sensor).filter(Sensor.id == update_data['sensor_id']).first()
        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
    
    for key, value in update_data.items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)

    # Broadcast to all clients
    await ws_manager.broadcast({
        "type": "alert_rules_changed",
        "action": "update",
        "rule": alert_rule_snapshot(db_rule)
    })

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="update",
        entity_type="alert_rule",
        entity_id=db_rule.id,
        before=before,
        after=alert_rule_snapshot(db_rule),
        ip_address=request.client.host if request and request.client else None
    )
    return db_rule


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    current_user=Depends(require_permission("alerts")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Delete an alert rule"""
    db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    before = alert_rule_snapshot(db_rule)
    db.delete(db_rule)
    db.commit()

    # Broadcast to all clients
    await ws_manager.broadcast({
        "type": "alert_rules_changed",
        "action": "delete",
        "rule_id": rule_id
    })

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="delete",
        entity_type="alert_rule",
        entity_id=rule_id,
        before=before,
        after=None,
        ip_address=request.client.host if request and request.client else None
    )
    return {"deleted": True}

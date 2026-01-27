"""
Alerts API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
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

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
    acknowledged: Optional[bool] = None,
    severity: Optional[str] = None,
    sensor_id: Optional[int] = None,
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
def get_active_alerts(db: Session = Depends(get_db)):
    """Get all unacknowledged alerts"""
    alerts = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).order_by(desc(Alert.created_at)).all()
    return alerts


@router.post("/{alert_id}/ack", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/ack-all")
def acknowledge_all_alerts(db: Session = Depends(get_db)):
    """Acknowledge all active alerts"""
    now = datetime.utcnow()
    result = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).update({
        "is_acknowledged": True,
        "acknowledged_at": now
    })
    db.commit()
    return {"acknowledged": result}


# Alert Rules
@router.get("/rules", response_model=List[AlertRuleResponse])
def get_alert_rules(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all alert rules"""
    query = db.query(AlertRule)
    if active_only:
        query = query.filter(AlertRule.is_active == True)
    rules = query.all()
    return rules


@router.post("/rules", response_model=AlertRuleResponse)
def create_alert_rule(rule: AlertRuleCreate, db: Session = Depends(get_db)):
    """Create a new alert rule"""
    # Verify sensor exists
    sensor = db.query(Sensor).filter(Sensor.id == rule.sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    # Validate condition
    valid_conditions = ['>', '<', '>=', '<=', '==', '!=']
    if rule.condition not in valid_conditions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid condition. Must be one of: {valid_conditions}"
        )
    
    db_rule = AlertRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(
    rule_id: int,
    rule: AlertRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update an alert rule"""
    db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    update_data = rule.model_dump(exclude_unset=True)
    
    # Validate condition if provided
    if 'condition' in update_data:
        valid_conditions = ['>', '<', '>=', '<=', '==', '!=']
        if update_data['condition'] not in valid_conditions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition. Must be one of: {valid_conditions}"
            )
    
    for key, value in update_data.items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/rules/{rule_id}")
def delete_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete an alert rule"""
    db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    db.delete(db_rule)
    db.commit()
    return {"deleted": True}

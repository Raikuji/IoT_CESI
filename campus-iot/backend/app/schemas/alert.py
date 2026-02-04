"""
Alert schemas for API validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertBase(BaseModel):
    sensor_id: int
    type: str
    message: Optional[str] = None
    severity: Optional[str] = "warning"


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    is_acknowledged: bool
    rule_id: Optional[int] = None
    escalation_level: Optional[int] = 0
    escalated_from_alert_id: Optional[int] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertRuleBase(BaseModel):
    name: Optional[str] = None
    sensor_id: Optional[int] = None
    sensor_type: Optional[str] = None
    room_id: Optional[str] = None
    condition: str
    threshold: float
    message: Optional[str] = None
    severity: Optional[str] = "warning"
    is_active: Optional[bool] = True
    active_days: Optional[list[int]] = None
    active_time_start: Optional[str] = None  # HH:MM
    active_time_end: Optional[str] = None    # HH:MM
    cooldown_minutes: Optional[int] = 5
    escalation_minutes: Optional[int] = None
    escalation_severity: Optional[str] = None


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    message: Optional[str] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    sensor_id: Optional[int] = None
    sensor_type: Optional[str] = None
    room_id: Optional[str] = None
    active_days: Optional[list[int]] = None
    active_time_start: Optional[str] = None
    active_time_end: Optional[str] = None
    cooldown_minutes: Optional[int] = None
    escalation_minutes: Optional[int] = None
    escalation_severity: Optional[str] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

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
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertRuleBase(BaseModel):
    sensor_id: int
    condition: str
    threshold: float
    message: Optional[str] = None
    severity: Optional[str] = "warning"


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    condition: Optional[str] = None
    threshold: Optional[float] = None
    message: Optional[str] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

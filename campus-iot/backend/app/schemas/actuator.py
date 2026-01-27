"""
Actuator schemas for API validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ActuatorBase(BaseModel):
    name: str
    type: str
    location: Optional[str] = "C101"


class ActuatorCreate(ActuatorBase):
    pass


class ActuatorResponse(ActuatorBase):
    id: int
    current_value: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActuatorCommand(BaseModel):
    value: int
    source: Optional[str] = "manual"


class ActuatorCommandResponse(BaseModel):
    id: int
    actuator_id: int
    command_value: int
    source: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class HeatingMode(BaseModel):
    mode: str  # "auto" or "manual"
    setpoint: Optional[float] = None  # target temperature for auto mode

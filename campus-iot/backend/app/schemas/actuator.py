"""
Actuator schemas for API validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ActuatorBase(BaseModel):
    name: str
    type: str
    location: Optional[str] = None


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
    mode: str  # "auto", "manual", "eco"
    setpoint: Optional[float] = None  # target temperature
    room: Optional[str] = None  # room/salle (e.g., "C101")


class RoomEnergyConfig(BaseModel):
    room: str
    mode: str  # "manual", "eco", "auto"
    setpoint: float  # target temperature
    eco_setpoint: Optional[float] = None  # temperature in eco mode (default: -2°C from normal)
    presence_timeout_minutes: int = 15  # auto switch to eco if no presence
    
    class Config:
        from_attributes = True


class RoomEnergyState(BaseModel):
    room: str
    mode: str
    setpoint: float
    eco_setpoint: float
    current_mode: str  # actual current mode (may be auto-switched to eco)
    has_presence: bool
    last_presence_time: Optional[datetime] = None
    presence_timeout_minutes: int

"""
Sensor schemas for API validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class SensorBase(BaseModel):
    name: str
    type: str
    location: Optional[str] = "C101"
    unit: Optional[str] = None


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None


class SensorResponse(SensorBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SensorDataBase(BaseModel):
    sensor_id: int
    value: float


class SensorDataCreate(SensorDataBase):
    pass


class SensorDataResponse(SensorDataBase):
    time: datetime
    
    class Config:
        from_attributes = True


class SensorWithLatestData(SensorResponse):
    latest_value: Optional[float] = None
    latest_time: Optional[datetime] = None

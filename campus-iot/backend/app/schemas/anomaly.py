"""
Anomaly schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict


class AnomalyResponse(BaseModel):
    id: int
    sensor_id: Optional[int] = None
    anomaly_type: str
    message: Optional[str] = None
    severity: str
    metadata: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

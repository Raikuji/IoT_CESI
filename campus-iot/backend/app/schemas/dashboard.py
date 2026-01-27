"""
Dashboard schemas for API validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class SensorSummary(BaseModel):
    sensor_id: int
    name: str
    type: str
    unit: Optional[str]
    latest_value: Optional[float]
    latest_time: Optional[datetime]
    status: str  # "ok", "warning", "danger", "offline"


class DashboardSummary(BaseModel):
    sensors: List[SensorSummary]
    active_alerts: int
    total_sensors: int
    online_sensors: int
    heating_status: Dict[str, Any]


class StatsRequest(BaseModel):
    sensor_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    interval: Optional[str] = "1h"  # 1m, 5m, 15m, 1h, 1d


class StatsResponse(BaseModel):
    sensor_id: int
    min_value: float
    max_value: float
    avg_value: float
    count: int
    data_points: List[Dict[str, Any]]


class PresenceStats(BaseModel):
    total_entries: int
    total_exits: int
    current_presence: bool
    last_change: Optional[datetime]
    history: List[Dict[str, Any]]

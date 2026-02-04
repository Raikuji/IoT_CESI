"""
Anomaly schemas
"""
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, Dict


class AnomalyResponse(BaseModel):
    id: int
    sensor_id: Optional[int] = None
    anomaly_type: str
    message: Optional[str] = None
    severity: str
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

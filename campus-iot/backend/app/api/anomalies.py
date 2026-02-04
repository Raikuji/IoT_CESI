"""
Anomalies API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from db import get_db
from models import Anomaly
from schemas.anomaly import AnomalyResponse
from api.auth import require_permission

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get("", response_model=List[AnomalyResponse])
async def get_anomalies(
    limit: int = Query(default=100, le=500),
    anomaly_type: Optional[str] = None,
    sensor_id: Optional[int] = None,
    severity: Optional[str] = None,
    current_user=Depends(require_permission("alerts")),
    db: Session = Depends(get_db)
):
    query = db.query(Anomaly)
    if anomaly_type:
        query = query.filter(Anomaly.anomaly_type == anomaly_type)
    if sensor_id:
        query = query.filter(Anomaly.sensor_id == sensor_id)
    if severity:
        query = query.filter(Anomaly.severity == severity)

    anomalies = query.order_by(desc(Anomaly.created_at)).limit(limit).all()
    return anomalies

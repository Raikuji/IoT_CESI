"""
Dashboard API endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from db import get_db
from models import Sensor, SensorData, Alert, Actuator
from schemas import DashboardSummary, SensorSummary, StatsResponse, PresenceStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary with all sensor latest values"""
    sensors = db.query(Sensor).filter(Sensor.is_active == True).all()
    
    sensor_summaries = []
    online_count = 0
    
    for sensor in sensors:
        # Get latest data point
        latest = db.query(SensorData).filter(
            SensorData.sensor_id == sensor.id
        ).order_by(desc(SensorData.time)).first()
        
        # Determine status
        status = "offline"
        if latest:
            age = datetime.utcnow() - latest.time.replace(tzinfo=None)
            if age < timedelta(minutes=5):
                status = "ok"
                online_count += 1
            elif age < timedelta(minutes=30):
                status = "warning"
                online_count += 1
        
        sensor_summaries.append(SensorSummary(
            sensor_id=sensor.id,
            name=sensor.name,
            type=sensor.type,
            unit=sensor.unit,
            latest_value=latest.value if latest else None,
            latest_time=latest.time if latest else None,
            status=status
        ))
    
    # Get active alerts count
    active_alerts = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).count()
    
    # Get heating status
    heating = db.query(Actuator).filter(Actuator.type == "servo").first()
    heating_status = {
        "current_value": heating.current_value if heating else 0,
        "mode": "manual",  # Could be stored in DB
        "setpoint": 21.0
    }
    
    return DashboardSummary(
        sensors=sensor_summaries,
        active_alerts=active_alerts,
        total_sensors=len(sensors),
        online_sensors=online_count,
        heating_status=heating_status
    )


@router.get("/stats", response_model=List[StatsResponse])
def get_stats(
    sensor_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    interval: str = Query(default="1h", regex="^(1m|5m|15m|1h|1d)$"),
    db: Session = Depends(get_db)
):
    """Get aggregated statistics for sensors"""
    # Default time range: last 24 hours
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)
    
    # Get sensors to query
    if sensor_id:
        sensors = db.query(Sensor).filter(Sensor.id == sensor_id).all()
    else:
        sensors = db.query(Sensor).filter(Sensor.is_active == True).all()
    
    results = []
    
    for sensor in sensors:
        # Get aggregated data
        query = db.query(
            func.min(SensorData.value).label('min_value'),
            func.max(SensorData.value).label('max_value'),
            func.avg(SensorData.value).label('avg_value'),
            func.count(SensorData.value).label('count')
        ).filter(
            SensorData.sensor_id == sensor.id,
            SensorData.time >= start_time,
            SensorData.time <= end_time
        )
        
        agg = query.first()
        
        # Get data points for charting
        data_points = db.query(SensorData).filter(
            SensorData.sensor_id == sensor.id,
            SensorData.time >= start_time,
            SensorData.time <= end_time
        ).order_by(SensorData.time).all()
        
        results.append(StatsResponse(
            sensor_id=sensor.id,
            min_value=agg.min_value or 0,
            max_value=agg.max_value or 0,
            avg_value=agg.avg_value or 0,
            count=agg.count or 0,
            data_points=[
                {"time": dp.time.isoformat(), "value": dp.value}
                for dp in data_points
            ]
        ))
    
    return results


@router.get("/presence", response_model=PresenceStats)
def get_presence_stats(
    hours: int = Query(default=24, le=168),
    db: Session = Depends(get_db)
):
    """Get presence detection statistics"""
    # Find presence sensor
    presence_sensor = db.query(Sensor).filter(
        Sensor.type == "presence"
    ).first()
    
    if not presence_sensor:
        return PresenceStats(
            total_entries=0,
            total_exits=0,
            current_presence=False,
            last_change=None,
            history=[]
        )
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get presence data
    data = db.query(SensorData).filter(
        SensorData.sensor_id == presence_sensor.id,
        SensorData.time >= start_time
    ).order_by(SensorData.time).all()
    
    # Calculate entries and exits
    entries = 0
    exits = 0
    last_value = 0
    
    for point in data:
        if point.value == 1 and last_value == 0:
            entries += 1
        elif point.value == 0 and last_value == 1:
            exits += 1
        last_value = point.value
    
    # Get latest state
    latest = db.query(SensorData).filter(
        SensorData.sensor_id == presence_sensor.id
    ).order_by(desc(SensorData.time)).first()
    
    return PresenceStats(
        total_entries=entries,
        total_exits=exits,
        current_presence=bool(latest.value) if latest else False,
        last_change=latest.time if latest else None,
        history=[
            {"time": dp.time.isoformat(), "presence": bool(dp.value)}
            for dp in data[-100:]  # Last 100 points
        ]
    )

"""
Sensors API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from db import get_db
from models import Sensor, SensorData
from schemas import (
    SensorCreate, SensorUpdate, SensorResponse,
    SensorDataCreate, SensorDataResponse, SensorWithLatestData
)

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get("/", response_model=List[SensorWithLatestData])
def get_sensors(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all sensors with their latest data"""
    query = db.query(Sensor)
    if active_only:
        query = query.filter(Sensor.is_active == True)
    sensors = query.offset(skip).limit(limit).all()
    
    result = []
    for sensor in sensors:
        # Get latest data point
        latest = db.query(SensorData).filter(
            SensorData.sensor_id == sensor.id
        ).order_by(desc(SensorData.time)).first()
        
        sensor_data = SensorWithLatestData(
            id=sensor.id,
            name=sensor.name,
            type=sensor.type,
            location=sensor.location,
            unit=sensor.unit,
            is_active=sensor.is_active,
            created_at=sensor.created_at,
            latest_value=latest.value if latest else None,
            latest_time=latest.time if latest else None
        )
        result.append(sensor_data)
    
    return result


@router.get("/{sensor_id}", response_model=SensorWithLatestData)
def get_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Get a specific sensor by ID"""
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    latest = db.query(SensorData).filter(
        SensorData.sensor_id == sensor.id
    ).order_by(desc(SensorData.time)).first()
    
    return SensorWithLatestData(
        id=sensor.id,
        name=sensor.name,
        type=sensor.type,
        location=sensor.location,
        unit=sensor.unit,
        is_active=sensor.is_active,
        created_at=sensor.created_at,
        latest_value=latest.value if latest else None,
        latest_time=latest.time if latest else None
    )


@router.post("/", response_model=SensorResponse)
def create_sensor(sensor: SensorCreate, db: Session = Depends(get_db)):
    """Create a new sensor"""
    db_sensor = Sensor(**sensor.model_dump())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


@router.patch("/{sensor_id}", response_model=SensorResponse)
def update_sensor(
    sensor_id: int,
    sensor: SensorUpdate,
    db: Session = Depends(get_db)
):
    """Update a sensor"""
    db_sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not db_sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    update_data = sensor.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sensor, key, value)
    
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


@router.get("/{sensor_id}/data", response_model=List[SensorDataResponse])
def get_sensor_data(
    sensor_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=1000, le=10000),
    db: Session = Depends(get_db)
):
    """Get historical data for a sensor"""
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    query = db.query(SensorData).filter(SensorData.sensor_id == sensor_id)
    
    if start_time:
        query = query.filter(SensorData.time >= start_time)
    if end_time:
        query = query.filter(SensorData.time <= end_time)
    
    # Default to last 24 hours if no time range specified
    if not start_time and not end_time:
        query = query.filter(SensorData.time >= datetime.utcnow() - timedelta(hours=24))
    
    data = query.order_by(desc(SensorData.time)).limit(limit).all()
    return data


@router.post("/{sensor_id}/data", response_model=SensorDataResponse)
def add_sensor_data(
    sensor_id: int,
    data: SensorDataCreate,
    db: Session = Depends(get_db)
):
    """Add a data point for a sensor (mainly for testing)"""
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    db_data = SensorData(sensor_id=sensor_id, value=data.value)
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

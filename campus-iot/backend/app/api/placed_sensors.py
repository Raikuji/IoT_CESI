"""
Placed Sensors API - Sensors placed on the building plan
Synced to Supabase for all users
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from db.database import get_db
from models.settings import PlacedSensor
from models.user import User
from api.auth import get_current_user
from services.websocket_manager import ws_manager

router = APIRouter(prefix="/placed-sensors", tags=["Placed Sensors"])


# Pydantic models
class PlacedSensorCreate(BaseModel):
    room_id: str
    sensor_type: str
    position_x: float = 0
    position_y: float = 0
    position_z: float = 0
    name: Optional[str] = None


class PlacedSensorUpdate(BaseModel):
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    name: Optional[str] = None
    current_value: Optional[float] = None
    status: Optional[str] = None


class PlacedSensorResponse(BaseModel):
    id: int
    room_id: str
    sensor_type: str
    position_x: float
    position_y: float
    position_z: float
    name: Optional[str]
    current_value: Optional[float]
    status: str
    placed_by_user_id: Optional[int]
    placed_by_email: Optional[str]
    created_at: str
    last_update: Optional[str]

    class Config:
        from_attributes = True


def sensor_to_response(sensor: PlacedSensor) -> PlacedSensorResponse:
    return PlacedSensorResponse(
        id=sensor.id,
        room_id=sensor.room_id,
        sensor_type=sensor.sensor_type,
        position_x=sensor.position_x or 0,
        position_y=sensor.position_y or 0,
        position_z=sensor.position_z or 0,
        name=sensor.name,
        current_value=sensor.current_value,
        status=sensor.status or "pending",
        placed_by_user_id=sensor.placed_by_user_id,
        placed_by_email=sensor.placed_by_email,
        created_at=sensor.created_at.isoformat() if sensor.created_at else datetime.utcnow().isoformat(),
        last_update=sensor.last_update.isoformat() if sensor.last_update else None
    )


@router.get("/", response_model=List[PlacedSensorResponse])
async def get_all_placed_sensors(
    room_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all placed sensors, optionally filtered by room or type"""
    query = db.query(PlacedSensor)
    
    if room_id:
        query = query.filter(PlacedSensor.room_id == room_id)
    if sensor_type:
        query = query.filter(PlacedSensor.sensor_type == sensor_type)
    
    sensors = query.order_by(PlacedSensor.created_at.desc()).all()
    return [sensor_to_response(s) for s in sensors]


@router.get("/{sensor_id}", response_model=PlacedSensorResponse)
async def get_placed_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Get a specific placed sensor"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor_to_response(sensor)


@router.post("/", response_model=PlacedSensorResponse, status_code=status.HTTP_201_CREATED)
async def create_placed_sensor(
    data: PlacedSensorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Place a new sensor on the building plan"""
    sensor = PlacedSensor(
        room_id=data.room_id,
        sensor_type=data.sensor_type,
        position_x=data.position_x,
        position_y=data.position_y,
        position_z=data.position_z,
        name=data.name,
        status="pending",
        placed_by_user_id=current_user.id,
        placed_by_email=current_user.email
    )
    
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    
    # Broadcast to all connected clients
    await ws_manager.broadcast({
        "type": "sensor_placed",
        "sensor": sensor_to_response(sensor).dict()
    })
    
    return sensor_to_response(sensor)


@router.put("/{sensor_id}", response_model=PlacedSensorResponse)
async def update_placed_sensor(
    sensor_id: int,
    data: PlacedSensorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a placed sensor position or value"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    if data.position_x is not None:
        sensor.position_x = data.position_x
    if data.position_y is not None:
        sensor.position_y = data.position_y
    if data.position_z is not None:
        sensor.position_z = data.position_z
    if data.name is not None:
        sensor.name = data.name
    if data.current_value is not None:
        sensor.current_value = data.current_value
        sensor.last_update = datetime.utcnow()
    if data.status is not None:
        sensor.status = data.status
    
    db.commit()
    db.refresh(sensor)
    
    # Broadcast update
    await ws_manager.broadcast({
        "type": "sensor_updated",
        "sensor": sensor_to_response(sensor).dict()
    })
    
    return sensor_to_response(sensor)


@router.delete("/{sensor_id}")
async def delete_placed_sensor(
    sensor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a placed sensor"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    room_id = sensor.room_id
    db.delete(sensor)
    db.commit()
    
    # Broadcast deletion
    await ws_manager.broadcast({
        "type": "sensor_removed",
        "sensor_id": sensor_id,
        "room_id": room_id
    })
    
    return {"success": True}


@router.post("/bulk", response_model=List[PlacedSensorResponse])
async def bulk_create_sensors(
    sensors: List[PlacedSensorCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple sensors at once"""
    created = []
    for data in sensors:
        sensor = PlacedSensor(
            room_id=data.room_id,
            sensor_type=data.sensor_type,
            position_x=data.position_x,
            position_y=data.position_y,
            position_z=data.position_z,
            name=data.name,
            status="pending",
            placed_by_user_id=current_user.id,
            placed_by_email=current_user.email
        )
        db.add(sensor)
        created.append(sensor)
    
    db.commit()
    
    # Refresh all
    for s in created:
        db.refresh(s)
    
    # Broadcast
    await ws_manager.broadcast({
        "type": "sensors_bulk_placed",
        "count": len(created)
    })
    
    return [sensor_to_response(s) for s in created]


@router.get("/room/{room_id}", response_model=List[PlacedSensorResponse])
async def get_room_sensors(room_id: str, db: Session = Depends(get_db)):
    """Get all sensors in a specific room"""
    sensors = db.query(PlacedSensor).filter(PlacedSensor.room_id == room_id).all()
    return [sensor_to_response(s) for s in sensors]

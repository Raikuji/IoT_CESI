"""
Placed Sensors API - Sensors placed on the building plan
Synced to Supabase for all users
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from db.database import get_db
from models.settings import PlacedSensor, SensorEnergySetting
from models.user import User
from api.auth import require_permission, require_any_permission
from services.websocket_manager import ws_manager
from services import mqtt_service
import json
from services.audit_service import log_audit

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


class SensorEnergySettingUpdate(BaseModel):
    energy_enabled: Optional[bool] = None
    refresh_interval: Optional[int] = None
    refresh_interval_night: Optional[int] = None
    disable_live: Optional[bool] = None
    profile: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    schedule_profile: Optional[str] = None
    schedule_days: Optional[list] = None
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None


class SensorEnergySettingResponse(BaseModel):
    placed_sensor_id: int
    energy_enabled: bool
    refresh_interval: int
    refresh_interval_night: int
    disable_live: bool
    profile: str
    schedule_enabled: bool
    schedule_profile: str
    schedule_days: list
    schedule_start: str
    schedule_end: str
    updated_at: Optional[str] = None

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


def placed_sensor_snapshot(sensor: PlacedSensor) -> dict:
    return {
        "id": sensor.id,
        "room_id": sensor.room_id,
        "sensor_type": sensor.sensor_type,
        "position_x": sensor.position_x,
        "position_y": sensor.position_y,
        "position_z": sensor.position_z,
        "name": sensor.name,
        "current_value": sensor.current_value,
        "status": sensor.status,
        "placed_by_user_id": sensor.placed_by_user_id,
        "placed_by_email": sensor.placed_by_email,
        "created_at": sensor.created_at.isoformat() if sensor.created_at else None,
        "last_update": sensor.last_update.isoformat() if sensor.last_update else None
    }


def energy_defaults() -> dict:
    return {
        "energy_enabled": False,
        "refresh_interval": 120,
        "refresh_interval_night": 300,
        "disable_live": True,
        "profile": "normal",
        "schedule_enabled": False,
        "schedule_profile": "eco",
        "schedule_days": [],
        "schedule_start": "22:00",
        "schedule_end": "06:00"
    }


def energy_to_response(setting: Optional[SensorEnergySetting], placed_sensor_id: int) -> SensorEnergySettingResponse:
    if not setting:
        defaults = energy_defaults()
        return SensorEnergySettingResponse(placed_sensor_id=placed_sensor_id, updated_at=None, **defaults)
    return SensorEnergySettingResponse(
        placed_sensor_id=placed_sensor_id,
        energy_enabled=setting.energy_enabled,
        refresh_interval=setting.refresh_interval,
        refresh_interval_night=setting.refresh_interval_night,
        disable_live=setting.disable_live,
        profile=setting.profile,
        schedule_enabled=setting.schedule_enabled,
        schedule_profile=setting.schedule_profile,
        schedule_days=setting.schedule_days or [],
        schedule_start=setting.schedule_start,
        schedule_end=setting.schedule_end,
        updated_at=setting.updated_at.isoformat() if setting.updated_at else None
    )


@router.get("/", response_model=List[PlacedSensorResponse])
async def get_all_placed_sensors(
    room_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    current_user: User = Depends(require_any_permission(["building", "dashboard"])),
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
async def get_placed_sensor(
    sensor_id: int,
    current_user: User = Depends(require_any_permission(["building", "dashboard"])),
    db: Session = Depends(get_db)
):
    """Get a specific placed sensor"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor_to_response(sensor)


@router.get("/{sensor_id}/energy", response_model=SensorEnergySettingResponse)
async def get_sensor_energy_setting(
    sensor_id: int,
    current_user: User = Depends(require_any_permission(["building", "dashboard"])),
    db: Session = Depends(get_db)
):
    """Get energy settings for a placed sensor"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    setting = db.query(SensorEnergySetting).filter(
        SensorEnergySetting.placed_sensor_id == sensor_id
    ).first()
    return energy_to_response(setting, sensor_id)


@router.put("/{sensor_id}/energy", response_model=SensorEnergySettingResponse)
async def update_sensor_energy_setting(
    sensor_id: int,
    data: SensorEnergySettingUpdate,
    current_user: User = Depends(require_any_permission(["building", "dashboard"])),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update energy settings for a placed sensor"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    setting = db.query(SensorEnergySetting).filter(
        SensorEnergySetting.placed_sensor_id == sensor_id
    ).first()

    before = None
    if not setting:
        defaults = energy_defaults()
        setting = SensorEnergySetting(placed_sensor_id=sensor_id, **defaults)
        db.add(setting)
    else:
        before = {
            "placed_sensor_id": setting.placed_sensor_id,
            "energy_enabled": setting.energy_enabled,
            "refresh_interval": setting.refresh_interval,
            "refresh_interval_night": setting.refresh_interval_night,
            "disable_live": setting.disable_live,
            "profile": setting.profile,
            "schedule_enabled": setting.schedule_enabled,
            "schedule_profile": setting.schedule_profile,
            "schedule_days": setting.schedule_days or [],
            "schedule_start": setting.schedule_start,
            "schedule_end": setting.schedule_end
        }

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(setting, key, value)

    db.commit()
    db.refresh(setting)

    response = energy_to_response(setting, sensor_id)

    await ws_manager.broadcast({
        "type": "sensor_energy_updated",
        "sensor_id": sensor_id,
        "settings": response.dict()
    })

    # Publish energy settings to MQTT (for devices/gateway)
    mqtt_payload = {
        "placed_sensor_id": sensor_id,
        "room_id": sensor.room_id,
        "sensor_type": sensor.sensor_type,
        "energy": {
            "enabled": response.energy_enabled,
            "refresh_interval": response.refresh_interval,
            "refresh_interval_night": response.refresh_interval_night,
            "disable_live": response.disable_live,
            "profile": response.profile,
            "schedule_enabled": response.schedule_enabled,
            "schedule_profile": response.schedule_profile,
            "schedule_days": response.schedule_days,
            "schedule_start": response.schedule_start,
            "schedule_end": response.schedule_end
        }
    }
    mqtt_service.publish(
        f"controls/energy/{sensor.room_id}/{sensor.sensor_type}",
        json.dumps(mqtt_payload),
        qos=1,
        retain=True
    )

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="update" if before else "create",
        entity_type="sensor_energy_setting",
        entity_id=setting.id,
        before=before,
        after=response.dict(),
        ip_address=request.client.host if request and request.client else None
    )

    return response


@router.post("/", response_model=PlacedSensorResponse, status_code=status.HTTP_201_CREATED)
async def create_placed_sensor(
    data: PlacedSensorCreate,
    current_user: User = Depends(require_permission("building")),
    db: Session = Depends(get_db),
    request: Request = None
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

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="create",
        entity_type="placed_sensor",
        entity_id=sensor.id,
        before=None,
        after=placed_sensor_snapshot(sensor),
        ip_address=request.client.host if request and request.client else None
    )
    
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
    current_user: User = Depends(require_permission("building")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update a placed sensor position or value"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    before = placed_sensor_snapshot(sensor)
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

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="update",
        entity_type="placed_sensor",
        entity_id=sensor.id,
        before=before,
        after=placed_sensor_snapshot(sensor),
        ip_address=request.client.host if request and request.client else None
    )
    
    # Broadcast update
    await ws_manager.broadcast({
        "type": "sensor_updated",
        "sensor": sensor_to_response(sensor).dict()
    })
    
    return sensor_to_response(sensor)


@router.delete("/{sensor_id}")
async def delete_placed_sensor(
    sensor_id: int,
    current_user: User = Depends(require_permission("building")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Remove a placed sensor"""
    sensor = db.query(PlacedSensor).filter(PlacedSensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    room_id = sensor.room_id
    before = placed_sensor_snapshot(sensor)
    db.delete(sensor)
    db.commit()

    log_audit(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="delete",
        entity_type="placed_sensor",
        entity_id=sensor_id,
        before=before,
        after=None,
        ip_address=request.client.host if request and request.client else None
    )
    
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
    current_user: User = Depends(require_permission("building")),
    db: Session = Depends(get_db),
    request: Request = None
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

    for s in created:
        log_audit(
            db=db,
            user_id=current_user.id,
            user_email=current_user.email,
            action="create",
            entity_type="placed_sensor",
            entity_id=s.id,
            before=None,
            after=placed_sensor_snapshot(s),
            ip_address=request.client.host if request and request.client else None
        )
    
    # Broadcast
    await ws_manager.broadcast({
        "type": "sensors_bulk_placed",
        "count": len(created)
    })
    
    return [sensor_to_response(s) for s in created]


@router.get("/room/{room_id}", response_model=List[PlacedSensorResponse])
async def get_room_sensors(
    room_id: str,
    current_user: User = Depends(require_any_permission(["building", "dashboard"])),
    db: Session = Depends(get_db)
):
    """Get all sensors in a specific room"""
    sensors = db.query(PlacedSensor).filter(PlacedSensor.room_id == room_id).all()
    return [sensor_to_response(s) for s in sensors]

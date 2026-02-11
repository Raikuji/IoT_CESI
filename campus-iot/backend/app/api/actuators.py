"""
Actuators API endpoints - Energy management by room
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict
from datetime import datetime

from db import get_db
from models import Actuator, ActuatorCommand as ActuatorCommandModel
from schemas import (
    ActuatorCreate, ActuatorResponse,
    ActuatorCommand, ActuatorCommandResponse, HeatingMode,
    RoomEnergyConfig, RoomEnergyState
)
from services import mqtt_service, energy_manager
from api.auth import require_permission

router = APIRouter(prefix="/actuators", tags=["actuators"])

# In-memory storage for backward compatibility
heating_state = {
    "mode": "manual",
    "setpoint": 21.0,
    "room": None
}


@router.get("/", response_model=List[ActuatorResponse])
def get_actuators(
    active_only: bool = True,
    current_user=Depends(require_permission("control")),
    db: Session = Depends(get_db)
):
    """Get all actuators"""
    query = db.query(Actuator)
    if active_only:
        query = query.filter(Actuator.is_active == True)
    actuators = query.all()
    return actuators


@router.get("/{actuator_id}", response_model=ActuatorResponse)
def get_actuator(
    actuator_id: int,
    current_user=Depends(require_permission("control")),
    db: Session = Depends(get_db)
):
    """Get a specific actuator"""
    actuator = db.query(Actuator).filter(Actuator.id == actuator_id).first()
    if not actuator:
        raise HTTPException(status_code=404, detail="Actuator not found")
    return actuator


@router.post("/{actuator_id}/command", response_model=ActuatorCommandResponse)
def send_command(
    actuator_id: int,
    command: ActuatorCommand,
    current_user=Depends(require_permission("control")),
    db: Session = Depends(get_db)
):
    """Send a command to an actuator"""
    actuator = db.query(Actuator).filter(Actuator.id == actuator_id).first()
    if not actuator:
        raise HTTPException(status_code=404, detail="Actuator not found")
    
    # Update actuator current value
    actuator.current_value = command.value
    
    # Log the command
    db_command = ActuatorCommandModel(
        actuator_id=actuator_id,
        command_value=command.value,
        source=command.source
    )
    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    
    # Publish to MQTT
    topic = f"actuators/{actuator.type}/set"
    mqtt_service.publish(topic, str(command.value))
    
    return db_command


@router.get("/{actuator_id}/commands", response_model=List[ActuatorCommandResponse])
def get_actuator_commands(
    actuator_id: int,
    limit: int = 50,
    current_user=Depends(require_permission("control")),
    db: Session = Depends(get_db)
):
    """Get command history for an actuator"""
    actuator = db.query(Actuator).filter(Actuator.id == actuator_id).first()
    if not actuator:
        raise HTTPException(status_code=404, detail="Actuator not found")
    
    commands = db.query(ActuatorCommandModel).filter(
        ActuatorCommandModel.actuator_id == actuator_id
    ).order_by(desc(ActuatorCommandModel.created_at)).limit(limit).all()
    
    return commands


# ============================================
# Heating control - Backward compatibility
# ============================================
@router.get("/heating/state")
def get_heating_state():
    """Get current heating state (mode, setpoint, room) - Public endpoint"""
    return heating_state


@router.post("/heating/mode", response_model=HeatingMode)
def set_heating_mode(
    mode: HeatingMode,
    current_user=Depends(require_permission("control"))
):
    """Set heating mode (auto/manual/eco) and setpoint for a room"""
    if mode.mode not in ["auto", "manual", "eco"]:
        raise HTTPException(
            status_code=400,
            detail="Mode must be 'auto', 'manual', or 'eco'"
        )
    
    if mode.setpoint is not None and (mode.setpoint < 10 or mode.setpoint > 30):
        raise HTTPException(
            status_code=400,
            detail="Setpoint must be between 10 and 30°C"
        )
    
    room = mode.room or "default"
    
    # Update in-memory state
    heating_state["mode"] = mode.mode
    if mode.setpoint is not None:
        heating_state["setpoint"] = mode.setpoint
    if mode.room is not None:
        heating_state["room"] = mode.room
    
    # Update energy manager for room-based management
    energy_manager.set_room_mode(
        room, 
        mode.mode, 
        mode.setpoint or 21.0
    )
    
    # Publish to MQTT (uniquement par salle)
    if room != "default":
        mqtt_service.publish(f"rooms/{room}/heating/mode", mode.mode, retain=True)
        if mode.setpoint:
            mqtt_service.publish(f"rooms/{room}/heating/setpoint", str(mode.setpoint), retain=True)
    
    return HeatingMode(**heating_state)


@router.get("/heating/setpoint")
def get_heating_setpoint():
    """Get heating temperature setpoint"""
    return {"setpoint": heating_state["setpoint"]}


@router.post("/heating/setpoint")
def set_heating_setpoint(
    room: str,
    setpoint: float,
    current_user=Depends(require_permission("control"))
):
    """Set heating temperature setpoint for a room"""
    if setpoint < 10 or setpoint > 30:
        raise HTTPException(
            status_code=400,
            detail="Setpoint must be between 10 and 30°C"
        )
    
    heating_state["setpoint"] = setpoint
    
    # Update energy manager
    energy_manager.set_room_mode(room, "manual", setpoint)
    
    # Publish to MQTT (sans préfixe car mqtt_service l'ajoute)
    topic = f"rooms/{room}/heating/setpoint"
    mqtt_service.publish(topic, str(setpoint), retain=True)
    
    return {"room": room, "setpoint": setpoint}


# ============================================
# Room-based Energy Management
# ============================================
@router.post("/rooms/{room}/energy/config")
def configure_room_energy(
    room: str,
    config: RoomEnergyConfig,
    current_user=Depends(require_permission("control"))
):
    """Configure energy management for a room"""
    try:
        energy_manager.initialize_room(
            room,
            mode=config.mode,
            setpoint=config.setpoint,
            eco_setpoint=config.eco_setpoint,
            presence_timeout_minutes=config.presence_timeout_minutes
        )
        return {"status": "success", "room": room, "config": config}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rooms/{room}/energy/state", response_model=RoomEnergyState)
def get_room_energy_state(room: str):
    """Get energy state for a room - Public endpoint"""
    state = energy_manager.get_room_state(room)
    return RoomEnergyState(**state)


@router.get("/rooms/energy/state")
def get_all_rooms_energy_state():
    """Get energy state for all rooms - Public endpoint"""
    return energy_manager.get_all_rooms_state()


@router.post("/rooms/{room}/heating/mode")
def set_room_heating_mode(
    room: str,
    mode: str = Query(..., description="Mode: manual, auto, or eco"),
    setpoint: float = Query(None, description="Target temperature"),
    current_user=Depends(require_permission("control"))
):
    """Set heating mode for a specific room"""
    try:
        energy_manager.set_room_mode(room, mode, setpoint)
        state = energy_manager.get_room_state(room)
        
        # Publish to MQTT (sans préfixe car mqtt_service l'ajoute)
        mqtt_service.publish(
            f"rooms/{room}/heating/mode",
            mode,
            retain=True
        )
        
        return {"status": "success", "room": room, "state": state}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rooms/{room}/presence")
def update_room_presence(
    room: str,
    has_presence: bool = Query(..., description="True if presence detected"),
    current_user=Depends(require_permission("control"))
):
    """Update presence detection for a room"""
    energy_manager.update_presence(room, has_presence)
    state = energy_manager.get_room_state(room)
    
    # Publish to MQTT (sans préfixe car mqtt_service l'ajoute)
    mqtt_service.publish(
        f"rooms/{room}/presence",
        "occupied" if has_presence else "empty",
        retain=True
    )
    
    return {"status": "success", "room": room, "has_presence": has_presence, "state": state}


@router.post("/rooms/{room}/eco-setpoint")
def set_room_eco_setpoint(
    room: str,
    eco_setpoint: float = Query(..., description="Eco mode temperature"),
    current_user=Depends(require_permission("control"))
):
    """Set eco mode temperature for a room"""
    if eco_setpoint < 10 or eco_setpoint > 30:
        raise HTTPException(
            status_code=400,
            detail="Eco setpoint must be between 10 and 30°C"
        )
    
    energy_manager.set_eco_setpoint(room, eco_setpoint)
    state = energy_manager.get_room_state(room)
    
    return {"status": "success", "room": room, "eco_setpoint": eco_setpoint, "state": state}

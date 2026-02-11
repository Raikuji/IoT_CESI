"""
Actuators API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from db import get_db
from models import Actuator, ActuatorCommand as ActuatorCommandModel
from schemas import (
    ActuatorCreate, ActuatorResponse,
    ActuatorCommand, ActuatorCommandResponse, HeatingMode
)
from services import mqtt_service
from api.auth import require_permission

router = APIRouter(prefix="/actuators", tags=["actuators"])

# In-memory storage for heating mode (could be moved to DB)
heating_state = {
    "mode": "manual",
    "setpoint": 21.0
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


# Heating specific endpoints
@router.get("/heating/state")
def get_heating_state():
    """Get current heating state (mode, setpoint, room)"""
    return heating_state


@router.get("/heating/mode", response_model=HeatingMode)
def get_heating_mode():
    """Get current heating mode"""
    return HeatingMode(**heating_state)


@router.post("/heating/mode", response_model=HeatingMode)
def set_heating_mode(mode: HeatingMode, current_user=Depends(require_permission("control"))):
    """Set heating mode (auto/manual) and setpoint"""
    if mode.mode not in ["auto", "manual"]:
        raise HTTPException(
            status_code=400,
            detail="Mode must be 'auto' or 'manual'"
        )
    
    heating_state["mode"] = mode.mode
    if mode.setpoint is not None:
        heating_state["setpoint"] = mode.setpoint
    if mode.room is not None:
        heating_state["room"] = mode.room
    
    # Publish mode change to MQTT
    mqtt_service.publish("actuators/heating/mode", mode.mode)
    if mode.setpoint:
        mqtt_service.publish("actuators/heating/setpoint", str(mode.setpoint))
    
    return HeatingMode(**heating_state)


@router.get("/heating/setpoint")
def get_heating_setpoint():
    """Get heating temperature setpoint"""
    return {"setpoint": heating_state["setpoint"]}


@router.post("/heating/setpoint")
def set_heating_setpoint(room: str, setpoint: float, current_user=Depends(require_permission("control"))):
    """Set heating temperature setpoint for a room"""
    if setpoint < 10 or setpoint > 30:
        raise HTTPException(
            status_code=400,
            detail="Setpoint must be between 10 and 30°C"
        )
    
    heating_state["setpoint"] = setpoint
    
    # Publish to MQTT with room and setpoint
    topic = f"campus/orion/actuators/heating"
    payload = {
        "room": room,
        "mode": "manual",
        "target": setpoint
    }
    mqtt_service.publish(topic, str(payload))
    
    return {"room": room, "setpoint": setpoint}

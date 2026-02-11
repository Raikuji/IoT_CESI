"""
Energy Management Service - Manages room-based heating economy modes
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from models.sensor import Sensor
from db.database import SessionLocal

logger = logging.getLogger(__name__)


class EnergyManager:
    """Manages energy efficiency per room with auto eco-mode based on presence detection"""
    
    def __init__(self):
        # Room configs: room_id -> {mode, setpoint, eco_setpoint, presence_timeout}
        self.room_configs: Dict[str, dict] = {}
        # Room states: room_id -> {current_mode, has_presence, last_presence_time}
        self.room_states: Dict[str, dict] = {}
    
    def initialize_room(self, room: str, mode: str = "manual", 
                       setpoint: float = 21.0, eco_setpoint: Optional[float] = None,
                       presence_timeout_minutes: int = 15):
        """Initialize or update room energy config"""
        if eco_setpoint is None:
            eco_setpoint = setpoint - 2  # Default eco mode is -2°C
        
        self.room_configs[room] = {
            "mode": mode,
            "setpoint": setpoint,
            "eco_setpoint": eco_setpoint,
            "presence_timeout_minutes": presence_timeout_minutes
        }
        
        if room not in self.room_states:
            self.room_states[room] = {
                "current_mode": mode,
                "has_presence": True,
                "last_presence_time": datetime.utcnow()
            }
        
        logger.info(f"Room {room} initialized: mode={mode}, setpoint={setpoint}°C, eco_setpoint={eco_setpoint}°C")
    
    def update_presence(self, room: str, has_presence: bool):
        """Update presence detection for a room"""
        if room not in self.room_configs:
            self.initialize_room(room)
        
        config = self.room_configs[room]
        
        if has_presence:
            self.room_states[room]["has_presence"] = True
            self.room_states[room]["last_presence_time"] = datetime.utcnow()
            
            # Si présence détectée ET mode configuré est ECO → passer en AUTO automatiquement
            if config["mode"] == "eco" and self.room_states[room]["current_mode"] == "eco":
                self.room_states[room]["current_mode"] = "auto"
                logger.info(f"Room {room}: Présence détectée (OUI), passage automatique de ECO → AUTO")
            # Sinon restaurer le mode configuré si on était en eco temporaire
            elif config["mode"] != "manual" and self.room_states[room]["current_mode"] == "eco":
                self.room_states[room]["current_mode"] = config["mode"]
                logger.info(f"Room {room}: Présence détectée, restauration du mode {config['mode']}")
        else:
            self.room_states[room]["has_presence"] = False
            logger.info(f"Room {room}: Pas de présence détectée")
    
    def check_auto_eco_mode(self, room: str) -> bool:
        """Check if room should auto-switch to eco mode based on presence timeout"""
        if room not in self.room_configs or room not in self.room_states:
            return False
        
        config = self.room_configs[room]
        state = self.room_states[room]
        
        # Only auto-switch if configured mode is not "manual"
        if config["mode"] == "manual":
            return False
        
        # Check if presence timeout exceeded
        if state["last_presence_time"]:
            timeout = config["presence_timeout_minutes"]
            time_since_presence = datetime.utcnow() - state["last_presence_time"]
            
            if time_since_presence > timedelta(minutes=timeout):
                # Auto-switch to eco mode
                if state["current_mode"] != "eco":
                    self.room_states[room]["current_mode"] = "eco"
                    logger.info(f"Room {room}: No presence for {timeout}min, auto-switching to eco mode")
                    return True
        
        return False
    
    def get_room_state(self, room: str) -> dict:
        """Get complete state for a room"""
        if room not in self.room_configs:
            self.initialize_room(room)
        
        # Check if auto eco-mode should be triggered
        self.check_auto_eco_mode(room)
        
        config = self.room_configs[room]
        state = self.room_states[room]
        
        # Get effective setpoint based on current mode
        effective_setpoint = config["setpoint"]
        if state["current_mode"] == "eco":
            effective_setpoint = config["eco_setpoint"]
        
        return {
            "room": room,
            "mode": config["mode"],  # configured mode
            "setpoint": config["setpoint"],
            "eco_setpoint": config["eco_setpoint"],
            "current_mode": state["current_mode"],  # actual current mode
            "has_presence": state["has_presence"],
            "last_presence_time": state["last_presence_time"],
            "presence_timeout_minutes": config["presence_timeout_minutes"],
            "effective_setpoint": effective_setpoint
        }
    
    def set_room_mode(self, room: str, mode: str, setpoint: Optional[float] = None):
        """Set room heating mode"""
        if mode not in ["manual", "auto", "eco"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'manual', 'auto', or 'eco'")
        
        if room not in self.room_configs:
            self.initialize_room(room, mode=mode, setpoint=setpoint or 21.0)
        
        self.room_configs[room]["mode"] = mode
        if setpoint is not None:
            self.room_configs[room]["setpoint"] = setpoint
        
        # Reset current mode to configured mode when manually setting
        self.room_states[room]["current_mode"] = mode
        
        logger.info(f"Room {room}: Mode set to {mode}, setpoint={self.room_configs[room]['setpoint']}°C")
    
    def set_eco_setpoint(self, room: str, eco_setpoint: float):
        """Set eco mode temperature"""
        if room not in self.room_configs:
            self.initialize_room(room)
        
        self.room_configs[room]["eco_setpoint"] = eco_setpoint
        logger.info(f"Room {room}: Eco setpoint set to {eco_setpoint}°C")
    
    def detect_presence_from_sensors(self, db_session=None):
        """Detect presence from movement sensors (ultrasonic/PIR)"""
        try:
            if not db_session:
                db_session = SessionLocal()
            
            # Get all rooms currently configured
            for room in list(self.room_configs.keys()):
                # Check for recent sensor data from this room
                # Look for ultrasonic or PIR sensors with recent readings
                recent_threshold = datetime.utcnow() - timedelta(minutes=5)
                
                has_recent_data = db_session.query(Sensor).filter(
                    Sensor.type.in_(["ultrasonic", "pir", "movement"]),
                    Sensor.room_id == room,
                    Sensor.last_reading_time >= recent_threshold
                ).first()
                
                if has_recent_data:
                    self.update_presence(room, True)
                else:
                    self.update_presence(room, False)
                    
        except Exception as e:
            logger.error(f"Error detecting presence from sensors: {e}")
    
    def get_all_rooms_state(self) -> dict:
        """Get state for all configured rooms"""
        return {room: self.get_room_state(room) for room in self.room_configs.keys()}


# Global instance
energy_manager = EnergyManager()

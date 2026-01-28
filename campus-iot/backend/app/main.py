"""
Campus IoT API - Main Application
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db import get_db, SessionLocal
from models import Sensor, SensorData, Alert, AlertRule
from services import mqtt_service, ws_manager
from api import (
    sensors_router,
    alerts_router,
    actuators_router,
    dashboard_router,
    auth_router,
    activity_router,
    reports_router
)
from api.security import router as security_router
from api.placed_sensors import router as placed_sensors_router
from api.settings import router as settings_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_mqtt_message(sensor_type: str, value, topic: str, room_id: str = "unknown"):
    """Handle incoming MQTT messages and store in database"""
    try:
        db = SessionLocal()
        
        logger.info(f"[HANDLER] Processing: room={room_id}, type={sensor_type}, value={value}")
        
        # Find or create sensor based on type and room
        sensor = db.query(Sensor).filter(
            Sensor.type == sensor_type,
            Sensor.location == room_id
        ).first()
        
        # If no sensor for this room, try to find by type only
        if not sensor:
            sensor = db.query(Sensor).filter(Sensor.type == sensor_type).first()
        
        if not sensor:
            # Auto-create sensor if it doesn't exist
            logger.info(f"Creating new sensor: {sensor_type} in {room_id}")
            sensor = Sensor(
                name=f"{sensor_type.capitalize()} {room_id}",
                type=sensor_type,
                location=room_id,
                status="online"
            )
            db.add(sensor)
            db.commit()
            db.refresh(sensor)
        else:
            # Update sensor status and location
            sensor.status = "online"
            sensor.location = room_id
            db.commit()
        
        # Store data point
        data_point = SensorData(
            sensor_id=sensor.id,
            value=float(value) if isinstance(value, (int, float, str)) else 0
        )
        db.add(data_point)
        db.commit()
        
        # Check alert rules
        rules = db.query(AlertRule).filter(
            AlertRule.sensor_id == sensor.id,
            AlertRule.is_active == True
        ).all()
        
        for rule in rules:
            triggered = False
            if rule.condition == '>' and float(value) > rule.threshold:
                triggered = True
            elif rule.condition == '<' and float(value) < rule.threshold:
                triggered = True
            elif rule.condition == '>=' and float(value) >= rule.threshold:
                triggered = True
            elif rule.condition == '<=' and float(value) <= rule.threshold:
                triggered = True
            elif rule.condition == '==' and float(value) == rule.threshold:
                triggered = True
            
            if triggered:
                alert = Alert(
                    sensor_id=sensor.id,
                    type=f"{sensor_type}_threshold",
                    message=rule.message or f"{sensor.name} threshold exceeded in {room_id}",
                    severity=rule.severity
                )
                db.add(alert)
                db.commit()
                logger.info(f"Alert triggered: {alert.message}")
                
                # Broadcast alert via WebSocket (async)
                asyncio.create_task(ws_manager.broadcast_alert({
                    "id": alert.id,
                    "sensor_id": sensor.id,
                    "room_id": room_id,
                    "type": alert.type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "created_at": alert.created_at.isoformat()
                }))
        
        db.close()
        
        # Broadcast sensor data via WebSocket (includes room info)
        asyncio.create_task(ws_manager.broadcast_sensor_data(
            sensor_type, value, datetime.utcnow().isoformat(), room_id
        ))
        
        logger.info(f"[HANDLER] Stored and broadcast: {sensor_type}={value} for {room_id}")
        
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Campus IoT API...")
    
    # Connect to MQTT broker
    mqtt_service.set_message_callback(handle_mqtt_message)
    mqtt_service.connect()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Campus IoT API...")
    mqtt_service.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API for Campus CESI IoT monitoring system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sensors_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(actuators_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(activity_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(placed_sensors_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "mqtt_connected": mqtt_service.connected
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mqtt": "connected" if mqtt_service.connected else "disconnected"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Could handle commands from frontend here
            logger.debug(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Campus IoT API - Main Application
"""
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from sqlalchemy import or_, desc

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db import get_db, SessionLocal
from models import Sensor, SensorData, Alert, AlertRule
from models.settings import PlacedSensor, SystemSetting
from models.anomaly import Anomaly
from services import mqtt_service, ws_manager
from services.backup_service import run_backup, cleanup_old_backups
from services.export_service import run_due_exports
from services.webhook_service import dispatch_webhooks
from api.activity import add_activity_log
from api import (
    sensors_router,
    alerts_router,
    actuators_router,
    dashboard_router,
    auth_router,
    activity_router,
    reports_router,
    backups_router,
    anomalies_router,
    integrations_router
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


def _parse_time(value: str):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except Exception:
        return None


def _is_rule_active(rule: AlertRule, now: datetime) -> bool:
    if rule.active_days:
        try:
            if now.weekday() not in rule.active_days:
                return False
        except Exception:
            pass

    if rule.active_time_start and rule.active_time_end:
        start = _parse_time(rule.active_time_start)
        end = _parse_time(rule.active_time_end)
        if start and end:
            now_t = now.time()
            if start <= end:
                if not (start <= now_t <= end):
                    return False
            else:
                # Overnight range
                if not (now_t >= start or now_t <= end):
                    return False

    return True


def _get_setting(db, key: str, default):
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting or setting.value is None:
            return default
        if setting.value_type == "number":
            return float(setting.value)
        if setting.value_type == "boolean":
            return str(setting.value).lower() in ("true", "1", "yes", "on")
        return setting.value
    except Exception:
        return default


def _detect_anomalies(db, sensor: Sensor, value: float, room_id: str):
    """Detect anomalies on latest sensor value"""
    # Settings
    min_samples = int(_get_setting(db, "anomaly_min_samples", 8))
    spike_z = float(_get_setting(db, "anomaly_spike_z", 3.0))
    stuck_window = int(_get_setting(db, "anomaly_stuck_window", 10))
    stuck_epsilon = float(_get_setting(db, "anomaly_stuck_epsilon", 0.001))
    drift_window = int(_get_setting(db, "anomaly_drift_window", 10))
    drift_slope = float(_get_setting(db, "anomaly_drift_slope", 0.05))
    cooldown_minutes = int(_get_setting(db, "anomaly_cooldown_minutes", 30))

    recent = db.query(SensorData).filter(
        SensorData.sensor_id == sensor.id
    ).order_by(desc(SensorData.time)).limit(max(stuck_window, drift_window, min_samples)).all()

    if len(recent) < min_samples:
        return

    values = [float(p.value) for p in reversed(recent)]

    def recently_reported(anomaly_type: str) -> bool:
        last = db.query(Anomaly).filter(
            Anomaly.sensor_id == sensor.id,
            Anomaly.anomaly_type == anomaly_type
        ).order_by(desc(Anomaly.created_at)).first()
        if not last or not last.created_at:
            return False
        last_time = last.created_at.replace(tzinfo=None)
        return (datetime.utcnow() - last_time).total_seconds() < (cooldown_minutes * 60)

    # Spike detection
    if not recently_reported("spike"):
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        if std > 0 and abs(value - mean) >= spike_z * std:
            message = f"Pic inhabituel détecté sur {sensor.name} en {room_id}"
            anomaly = Anomaly(
                sensor_id=sensor.id,
                anomaly_type="spike",
                message=message,
                severity="warning",
                metadata_json={"mean": mean, "std": std, "value": value}
            )
            db.add(anomaly)
            db.commit()
            dispatch_webhooks(db, "anomaly.detected", {
                "id": anomaly.id,
                "sensor_id": sensor.id,
                "room_id": room_id,
                "anomaly_type": anomaly.anomaly_type,
                "message": anomaly.message,
                "severity": anomaly.severity,
                "created_at": anomaly.created_at.isoformat() if anomaly.created_at else None,
                "metadata": anomaly.metadata_json
            })
            alert = Alert(
                sensor_id=sensor.id,
                type="anomaly_spike",
                message=message,
                severity="warning"
            )
            db.add(alert)
            db.commit()
            logger.info(f"Anomaly detected (spike): {message}")

    # Stuck detection
    if len(values) >= stuck_window and not recently_reported("stuck"):
        window = values[-stuck_window:]
        if max(window) - min(window) <= stuck_epsilon:
            message = f"Capteur bloqué détecté sur {sensor.name} en {room_id}"
            anomaly = Anomaly(
                sensor_id=sensor.id,
                anomaly_type="stuck",
                message=message,
                severity="warning",
                metadata_json={"window": stuck_window, "value": value}
            )
            db.add(anomaly)
            db.commit()
            dispatch_webhooks(db, "anomaly.detected", {
                "id": anomaly.id,
                "sensor_id": sensor.id,
                "room_id": room_id,
                "anomaly_type": anomaly.anomaly_type,
                "message": anomaly.message,
                "severity": anomaly.severity,
                "created_at": anomaly.created_at.isoformat() if anomaly.created_at else None,
                "metadata": anomaly.metadata_json
            })
            alert = Alert(
                sensor_id=sensor.id,
                type="anomaly_stuck",
                message=message,
                severity="warning"
            )
            db.add(alert)
            db.commit()
            logger.info(f"Anomaly detected (stuck): {message}")

    # Drift detection (linear trend over window)
    if len(values) >= drift_window and not recently_reported("drift"):
        window = values[-drift_window:]
        n = len(window)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(window) / n
        num = sum((x[i] - x_mean) * (window[i] - y_mean) for i in range(n))
        den = sum((x[i] - x_mean) ** 2 for i in range(n)) or 1
        slope = num / den
        if abs(slope) >= drift_slope:
            message = f"Dérive détectée sur {sensor.name} en {room_id}"
            anomaly = Anomaly(
                sensor_id=sensor.id,
                anomaly_type="drift",
                message=message,
                severity="info",
                metadata_json={"slope": slope, "window": drift_window}
            )
            db.add(anomaly)
            db.commit()
            dispatch_webhooks(db, "anomaly.detected", {
                "id": anomaly.id,
                "sensor_id": sensor.id,
                "room_id": room_id,
                "anomaly_type": anomaly.anomaly_type,
                "message": anomaly.message,
                "severity": anomaly.severity,
                "created_at": anomaly.created_at.isoformat() if anomaly.created_at else None,
                "metadata": anomaly.metadata_json
            })
            alert = Alert(
                sensor_id=sensor.id,
                type="anomaly_drift",
                message=message,
                severity="info"
            )
            db.add(alert)
            db.commit()
            logger.info(f"Anomaly detected (drift): {message}")


def handle_mqtt_message(sensor_type: str, value, topic: str, room_id: str = "unknown"):
    """Handle incoming MQTT messages and store in database
    
    The room_id comes directly from the MQTT payload {"room": "X101", "value": 23.5}
    This auto-assigns the sensor to the room specified by the Arduino/transmitter.
    """
    try:
        db = SessionLocal()
        
        logger.info(f"[HANDLER] Processing: room={room_id}, type={sensor_type}, value={value}")
        
        # Find sensor by type and room (exact match)
        sensor = db.query(Sensor).filter(
            Sensor.type == sensor_type,
            Sensor.location == room_id
        ).first()
        
        # If room is provided but no sensor exists for this room, create one
        # If room is "unknown", try to find any sensor of this type
        if not sensor and room_id == "unknown":
            sensor = db.query(Sensor).filter(Sensor.type == sensor_type).first()
        
        if not sensor:
            # Auto-create sensor with the room from payload
            logger.info(f"Creating new sensor: {sensor_type} in {room_id}")
            sensor = Sensor(
                name=f"{sensor_type.capitalize()} {room_id}" if room_id != "unknown" else f"{sensor_type.capitalize()} Auto",
                type=sensor_type,
                location=room_id if room_id != "unknown" else None,
                is_active=True
            )
            db.add(sensor)
            db.commit()
            db.refresh(sensor)
            
            # Also create a PlacedSensor for 3D visualization if room is known
            if room_id != "unknown":
                existing_placed = db.query(PlacedSensor).filter(
                    PlacedSensor.room_id == room_id,
                    PlacedSensor.sensor_type == sensor_type
                ).first()
                
                if not existing_placed:
                    placed_sensor = PlacedSensor(
                        room_id=room_id,
                        sensor_type=sensor_type,
                        position_x=0.5,  # Center of room
                        position_y=0.5,
                        name=f"{sensor_type.capitalize()} {room_id}",
                        current_value=float(value) if isinstance(value, (int, float, str)) else None,
                        status="ok"
                    )
                    db.add(placed_sensor)
                    db.commit()
                    logger.info(f"Created PlacedSensor for 3D: {sensor_type} in {room_id}")
        else:
            # Update sensor - ALWAYS update location if room is provided in payload
            sensor.is_active = True
            if room_id != "unknown":
                sensor.location = room_id
                sensor.name = f"{sensor_type.capitalize()} {room_id}"
                
                # Also update or create PlacedSensor
                placed_sensor = db.query(PlacedSensor).filter(
                    PlacedSensor.room_id == room_id,
                    PlacedSensor.sensor_type == sensor_type
                ).first()
                
                if placed_sensor:
                    placed_sensor.current_value = float(value) if isinstance(value, (int, float, str)) else None
                    placed_sensor.status = "ok"
                    placed_sensor.last_update = datetime.utcnow()
                else:
                    placed_sensor = PlacedSensor(
                        room_id=room_id,
                        sensor_type=sensor_type,
                        position_x=0.5,
                        position_y=0.5,
                        name=f"{sensor_type.capitalize()} {room_id}",
                        current_value=float(value) if isinstance(value, (int, float, str)) else None,
                        status="ok"
                    )
                    db.add(placed_sensor)
                    logger.info(f"Created PlacedSensor for 3D: {sensor_type} in {room_id}")
            db.commit()
        
        # Store data point
        data_point = SensorData(
            sensor_id=sensor.id,
            value=float(value) if isinstance(value, (int, float, str)) else 0
        )
        db.add(data_point)
        db.commit()
        
        # Check alert rules (sensor_id or sensor_type/room_id)
        rules = db.query(AlertRule).filter(
            AlertRule.is_active == True
        ).filter(
            or_(AlertRule.sensor_id == sensor.id, AlertRule.sensor_id.is_(None))
        ).all()

        now = datetime.utcnow()

        for rule in rules:
            if rule.sensor_id and rule.sensor_id != sensor.id:
                continue
            if rule.sensor_type and rule.sensor_type != sensor.type:
                continue
            if rule.room_id and rule.room_id != room_id:
                continue
            if not _is_rule_active(rule, now):
                continue

            # Cooldown check
            if rule.cooldown_minutes is not None:
                last_alert = db.query(Alert).filter(
                    Alert.rule_id == rule.id,
                    Alert.sensor_id == sensor.id
                ).order_by(desc(Alert.created_at)).first()
                if last_alert and last_alert.created_at:
                    last_time = last_alert.created_at.replace(tzinfo=None)
                    if (now - last_time).total_seconds() < (rule.cooldown_minutes * 60):
                        continue

            # Condition evaluation
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
            elif rule.condition == '!=' and float(value) != rule.threshold:
                triggered = True

            if triggered:
                alert = Alert(
                    sensor_id=sensor.id,
                    rule_id=rule.id,
                    type=f"{sensor_type}_threshold",
                    message=rule.message or f"{sensor.name} seuil dépassé en {room_id}",
                    severity=rule.severity,
                    escalation_level=0
                )
                db.add(alert)
                db.commit()
                logger.info(f"Alert triggered: {alert.message}")

                dispatch_webhooks(db, "alert.triggered", {
                    "id": alert.id,
                    "sensor_id": sensor.id,
                    "room_id": room_id,
                    "type": alert.type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None
                })

                # Broadcast alert via WebSocket (async-safe)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(ws_manager.broadcast_alert({
                        "id": alert.id,
                        "sensor_id": sensor.id,
                        "room_id": room_id,
                        "type": alert.type,
                        "message": alert.message,
                        "severity": alert.severity,
                        "created_at": alert.created_at.isoformat(),
                        "rule_id": alert.rule_id
                    }))
                except RuntimeError:
                    asyncio.run(ws_manager.broadcast_alert({
                        "id": alert.id,
                        "sensor_id": sensor.id,
                        "room_id": room_id,
                        "type": alert.type,
                        "message": alert.message,
                        "severity": alert.severity,
                        "created_at": alert.created_at.isoformat(),
                        "rule_id": alert.rule_id
                    }))

            # Escalation check (if unacknowledged and overdue)
            if rule.escalation_minutes and rule.escalation_severity:
                open_alerts = db.query(Alert).filter(
                    Alert.rule_id == rule.id,
                    Alert.sensor_id == sensor.id,
                    Alert.is_acknowledged == False
                ).order_by(desc(Alert.created_at)).all()

                for open_alert in open_alerts:
                    if open_alert.escalation_level and open_alert.escalation_level >= 1:
                        continue
                    if not open_alert.created_at:
                        continue

                    age = now - open_alert.created_at.replace(tzinfo=None)
                    if age >= timedelta(minutes=rule.escalation_minutes):
                        open_alert.escalation_level = 1
                        db.commit()

                        escalated = Alert(
                            sensor_id=sensor.id,
                            rule_id=rule.id,
                            type=f"{sensor_type}_escalation",
                            message=f"Escalade: {open_alert.message}",
                            severity=rule.escalation_severity,
                            escalation_level=1,
                            escalated_from_alert_id=open_alert.id
                        )
                        db.add(escalated)
                        db.commit()

                        dispatch_webhooks(db, "alert.escalated", {
                            "id": escalated.id,
                            "sensor_id": sensor.id,
                            "room_id": room_id,
                            "type": escalated.type,
                            "message": escalated.message,
                            "severity": escalated.severity,
                            "created_at": escalated.created_at.isoformat() if escalated.created_at else None,
                            "escalated_from_alert_id": escalated.escalated_from_alert_id
                        })

                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(ws_manager.broadcast_alert({
                                "id": escalated.id,
                                "sensor_id": sensor.id,
                                "room_id": room_id,
                                "type": escalated.type,
                                "message": escalated.message,
                                "severity": escalated.severity,
                                "created_at": escalated.created_at.isoformat(),
                                "rule_id": escalated.rule_id,
                                "escalated_from_alert_id": escalated.escalated_from_alert_id
                            }))
                        except RuntimeError:
                            asyncio.run(ws_manager.broadcast_alert({
                                "id": escalated.id,
                                "sensor_id": sensor.id,
                                "room_id": room_id,
                                "type": escalated.type,
                                "message": escalated.message,
                                "severity": escalated.severity,
                                "created_at": escalated.created_at.isoformat(),
                                "rule_id": escalated.rule_id,
                                "escalated_from_alert_id": escalated.escalated_from_alert_id
                            }))

        # Anomaly detection
        try:
            _detect_anomalies(db, sensor, float(value), room_id)
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
        
        db.close()
        
        # Broadcast sensor data via WebSocket (async-safe)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast_sensor_data(
                sensor_type, value, datetime.utcnow().isoformat(), room_id
            ))
        except RuntimeError:
            # No running loop - skip broadcast (will be picked up on next poll)
            pass
        
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
    
    backup_task = None
    export_task = None
    if settings.backups_enabled and settings.backup_interval_minutes > 0:
        async def backup_loop():
            await asyncio.sleep(10)
            while True:
                try:
                    await asyncio.to_thread(run_backup)
                    if settings.backup_retention_days > 0:
                        await asyncio.to_thread(cleanup_old_backups, settings.backup_retention_days)
                    logger.info("Automatic backup completed")
                except Exception as e:
                    logger.error(f"Automatic backup failed: {e}")
                await asyncio.sleep(settings.backup_interval_minutes * 60)

        backup_task = asyncio.create_task(backup_loop())

    if settings.exports_enabled and settings.export_check_interval_seconds > 0:
        async def export_loop():
            await asyncio.sleep(5)
            while True:
                try:
                    def _run_exports():
                        db = SessionLocal()
                        try:
                            run_due_exports(db)
                        finally:
                            db.close()

                    await asyncio.to_thread(_run_exports)
                    logger.info("Export check completed")
                except Exception as e:
                    logger.error(f"Export check failed: {e}")
                await asyncio.sleep(settings.export_check_interval_seconds)

        export_task = asyncio.create_task(export_loop())

    yield
    
    # Shutdown
    logger.info("Shutting down Campus IoT API...")
    if backup_task:
        backup_task.cancel()
    if export_task:
        export_task.cancel()
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
app.include_router(backups_router, prefix="/api")
app.include_router(anomalies_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
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

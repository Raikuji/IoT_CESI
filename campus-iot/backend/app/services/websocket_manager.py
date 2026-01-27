"""
WebSocket manager for real-time updates
"""
import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_sensor_data(self, sensor_type: str, value: Any, timestamp: str = None, room_id: str = None):
        """Broadcast sensor data update"""
        message = {
            "type": "sensor_data",
            "data": {
                "sensor_type": sensor_type,
                "value": value,
                "timestamp": timestamp,
                "room_id": room_id
            }
        }
        logger.info(f"[WS] Broadcasting: {sensor_type}={value} for room {room_id}")
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcast a new alert"""
        message = {
            "type": "alert",
            "data": alert_data
        }
        await self.broadcast(message)
    
    async def broadcast_actuator_status(self, actuator_id: int, value: int):
        """Broadcast actuator status update"""
        message = {
            "type": "actuator_status",
            "data": {
                "actuator_id": actuator_id,
                "value": value
            }
        }
        await self.broadcast(message)


# Singleton instance
ws_manager = WebSocketManager()

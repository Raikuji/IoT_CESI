"""
MQTT Client service for receiving sensor data
"""
import json
import logging
from typing import Callable, Optional
import paho.mqtt.client as mqtt
from config import settings

logger = logging.getLogger(__name__)


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.message_callback: Optional[Callable] = None
        self.connected = False
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info(f"Connected to MQTT broker at {settings.mqtt_broker}:{settings.mqtt_port}")
            self.connected = True
            # Subscribe to all sensor topics
            # Format: campus/orion/sensors/#
            topic = f"{settings.mqtt_topic_prefix}/sensors/#"
            client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.info(f"[MQTT] Received: {topic} = {payload}")
            
            # Parse the message
            try:
                value = float(payload)
            except ValueError:
                try:
                    data = json.loads(payload)
                    value = data.get('value', data)
                except json.JSONDecodeError:
                    value = payload
            
            # Extract room and sensor type from topic
            # Format: campus/orion/{ROOM}/sensors/{TYPE}
            # Example: campus/orion/X101/sensors/temperature
            parts = topic.split('/')
            if len(parts) >= 5:
                room_id = parts[2]      # X101, X108, NUMERILAB, etc.
                sensor_type = parts[4]  # temperature, humidity, presence
            else:
                room_id = "unknown"
                sensor_type = parts[-1] if len(parts) > 0 else "unknown"
            
            logger.info(f"[MQTT] Room: {room_id}, Type: {sensor_type}, Value: {value}")
            
            # Call the callback if set
            if self.message_callback:
                self.message_callback(sensor_type, value, topic, room_id)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def set_message_callback(self, callback: Callable):
        """Set callback function for incoming messages"""
        self.message_callback = callback
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
            self.client.loop_start()
            logger.info("MQTT client started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client stopped")
    
    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False):
        """Publish a message to MQTT broker"""
        full_topic = f"{settings.mqtt_topic_prefix}/{topic}"
        result = self.client.publish(full_topic, payload, qos=qos, retain=retain)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published to {full_topic}: {payload}")
        else:
            logger.error(f"Failed to publish to {full_topic}: {result.rc}")
        return result


# Singleton instance
mqtt_service = MQTTService()

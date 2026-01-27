#!/usr/bin/env python3

import time
import sys
import threading
import json
import re

try:
    import serial
except ImportError:
    print("Missing pyserial. Run: pip install pyserial")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Missing paho-mqtt. Run: pip install paho-mqtt")
    sys.exit(1)

# =============================================================================
# CONFIGURATION - MODIFY THESE VALUES
# =============================================================================

# Serial port of your Arduino Gateway
# Find it with: ls /dev/cu.usb* (macOS) or ls /dev/ttyUSB* (Linux) or check Arduino IDE
# macOS examples: /dev/cu.usbmodem14101, /dev/cu.usbserial-1420
# Windows examples: COM3, COM4
# Linux examples: /dev/ttyUSB0, /dev/ttyACM0
SERIAL_PORT = "/dev/cu.usbmodem14101"  # <-- CHANGE THIS TO YOUR PORT
SERIAL_BAUD = 9600

# MQTT Broker - localhost because Mosquitto runs in Docker
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# MQTT Settings (same as web app backend)
QOS = 1
RETAIN = True
CLEAN_SESSION = False

# Default room (used for direct publishing, gateway handles its own room)
DEFAULT_ROOM = "X101"

# Topic structure: campus/orion/{ROOM}/sensors/{TYPE}
TOPIC_PREFIX = "campus/orion"
TOPIC_COMMANDS = f"{TOPIC_PREFIX}/+/actuators/#"

# =============================================================================
# GLOBALS
# =============================================================================

ser = None  # serial connection


# =============================================================================
# MQTT CALLBACKS
# =============================================================================

def on_connect(client, userdata, flags, rc):
    """Called when we connect to MQTT broker"""
    if rc == 0:
        print(f"[MQTT] Connected to {MQTT_BROKER}:{MQTT_PORT}")
        print(f"[MQTT] QoS={QOS}, Retain={RETAIN}, CleanSession={CLEAN_SESSION}")
        
        # Subscribe to actuator commands to forward to Arduino
        client.subscribe(TOPIC_COMMANDS, qos=QOS)
        print(f"[MQTT] Subscribed: {TOPIC_COMMANDS}")
    else:
        print(f"[MQTT] Connection failed (code: {rc})")


def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnected (code: {rc})")


def on_message(client, userdata, msg):
    """Called when we receive an MQTT message (actuator commands from web app)"""
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"[MQTT->Serial] {topic}: {payload}")
    
    # Forward command to Arduino gateway
    if ser and ser.is_open:
        command = f"CMD:{topic}:{payload}\n"
        ser.write(command.encode())
        print(f"[Serial] Sent: {command.strip()}")


# =============================================================================
# SERIAL READING THREAD
# =============================================================================

def read_serial(client):
    """
    Continuously reads from Arduino serial.
    When Arduino sends "MQTT:topic:payload", we publish to Mosquitto.
    """
    global ser
    
    while True:
        try:
            if ser and ser.is_open and ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line.startswith("MQTT:"):
                    # Format: MQTT:campus/orion/X101/sensors/temperature:23.5
                    parts = line.split(":", 2)
                    if len(parts) == 3:
                        topic = parts[1]
                        payload = parts[2]
                        
                        # Publish to Mosquitto
                        result = client.publish(topic, payload, qos=QOS, retain=RETAIN)
                        
                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            print(f"[Serial->MQTT] {topic} = {payload}")
                        else:
                            print(f"[Error] Failed to publish: {result.rc}")
                    else:
                        print(f"[Warning] Invalid MQTT format: {line}")
                
                elif line:
                    # Debug output from Arduino
                    print(f"[Arduino] {line}")
            
            time.sleep(0.01)
            
        except Exception as e:
            print(f"[Error] Serial read: {e}")
            time.sleep(1)


# =============================================================================
# TERMINAL INPUT THREAD (for testing)
# =============================================================================

def read_terminal(client):
    """
    Reads keyboard input for testing without physical sensors.
    """
    global ser
    
    print()
    print("=" * 60)
    print("TESTING COMMANDS (type and press Enter):")
    print("=" * 60)
    print()
    print("SENSORS (publish data):")
    print("  temp 23.5          -> temperature")
    print("  hum 45             -> humidity")
    print("  pres 1             -> presence (1=yes, 0=no)")
    print("  light 75           -> light level (0-100)")
    print()
    print("ACTUATORS (send commands):")
    print("  motor 50           -> motor position (0-100)")
    print("  motor open/close   -> motor shortcuts")
    print("  speaker beep       -> single beep")
    print("  speaker warning    -> warning sound")
    print("  speaker danger     -> alarm sound")
    print("  speaker co2        -> CO2 alert")
    print("  speaker stop       -> silence")
    print()
    print("ADVANCED:")
    print("  pub X108 temp 22   -> publish to specific room")
    print("  cmd X108 motor 75  -> send command to specific room")
    print("  raw topic value    -> publish to any topic")
    print("  help               -> show this help")
    print("  quit               -> exit")
    print("=" * 60)
    print()
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            cmd = user_input.lower()
            
            if cmd == 'quit' or cmd == 'exit':
                print("Bye!")
                sys.exit(0)
            
            elif cmd == 'help':
                print("Commands: temp, hum, pres, light, motor, speaker, pub, cmd, raw, quit")
            
            # ==================== SENSORS ====================
            
            elif user_input.startswith("temp "):
                value = user_input.split()[1]
                topic = f"{TOPIC_PREFIX}/{DEFAULT_ROOM}/sensors/temperature"
                client.publish(topic, value, qos=QOS, retain=RETAIN)
                print(f"[Sensor] Temperature = {value}°C")
            
            elif user_input.startswith("hum "):
                value = user_input.split()[1]
                topic = f"{TOPIC_PREFIX}/{DEFAULT_ROOM}/sensors/humidity"
                client.publish(topic, value, qos=QOS, retain=RETAIN)
                print(f"[Sensor] Humidity = {value}%")
            
            elif user_input.startswith("pres "):
                value = user_input.split()[1]
                topic = f"{TOPIC_PREFIX}/{DEFAULT_ROOM}/sensors/presence"
                client.publish(topic, value, qos=QOS, retain=RETAIN)
                print(f"[Sensor] Presence = {'Yes' if value == '1' else 'No'}")
            
            elif user_input.startswith("light "):
                value = user_input.split()[1]
                topic = f"{TOPIC_PREFIX}/{DEFAULT_ROOM}/sensors/light"
                client.publish(topic, value, qos=QOS, retain=RETAIN)
                print(f"[Sensor] Light = {value}%")
            
            # ==================== ACTUATORS ====================
            
            elif user_input.startswith("motor "):
                value = user_input.split()[1]
                # Send command to actuator
                topic = f"{TOPIC_PREFIX}/{DEFAULT_ROOM}/actuators/motor"
                client.publish(topic, value, qos=QOS, retain=False)
                print(f"[Actuator] Motor command: {value}")
                
                # Also forward to Arduino if connected
                if ser and ser.is_open:
                    cmd_str = f"CMD:{topic}:{value}\n"
                    ser.write(cmd_str.encode())
            
            elif user_input.startswith("speaker "):
                value = user_input.split()[1]
                topic = f"{TOPIC_PREFIX}/{DEFAULT_ROOM}/actuators/speaker"
                client.publish(topic, value, qos=QOS, retain=False)
                print(f"[Actuator] Speaker command: {value}")
                
                if ser and ser.is_open:
                    cmd_str = f"CMD:{topic}:{value}\n"
                    ser.write(cmd_str.encode())
            
            # ==================== ADVANCED ====================
            
            # Publish sensor to specific room: pub ROOM TYPE VALUE
            elif user_input.startswith("pub "):
                parts = user_input.split()
                if len(parts) >= 4:
                    room = parts[1]
                    sensor_type = parts[2]
                    value = parts[3]
                    topic = f"{TOPIC_PREFIX}/{room}/sensors/{sensor_type}"
                    client.publish(topic, value, qos=QOS, retain=RETAIN)
                    print(f"[Published] {room}/{sensor_type} = {value}")
                else:
                    print("Usage: pub ROOM TYPE VALUE (e.g., pub X108 temp 22)")
            
            # Send command to specific room: cmd ROOM ACTUATOR VALUE
            elif user_input.startswith("cmd "):
                parts = user_input.split()
                if len(parts) >= 4:
                    room = parts[1]
                    actuator = parts[2]
                    value = parts[3]
                    topic = f"{TOPIC_PREFIX}/{room}/actuators/{actuator}"
                    client.publish(topic, value, qos=QOS, retain=False)
                    print(f"[Command] {room}/{actuator} = {value}")
                    
                    if ser and ser.is_open:
                        cmd_str = f"CMD:{topic}:{value}\n"
                        ser.write(cmd_str.encode())
                else:
                    print("Usage: cmd ROOM ACTUATOR VALUE (e.g., cmd X108 motor 50)")
            
            # Raw publish: raw topic value
            elif user_input.startswith("raw "):
                parts = user_input.split(None, 2)
                if len(parts) >= 3:
                    topic = parts[1]
                    value = parts[2]
                    client.publish(topic, value, qos=QOS, retain=RETAIN)
                    print(f"[Raw] {topic} = {value}")
                else:
                    print("Usage: raw topic value")
            
            # Send to Arduino serial
            elif user_input.startswith("DATA:"):
                if ser and ser.is_open:
                    ser.write((user_input + "\n").encode())
                    print(f"[->Serial] {user_input}")
                else:
                    print("[Error] Serial not connected")
            
            else:
                print("Unknown command. Type 'help' for list.")
                    
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Error] {e}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    global ser
    
    print()
    print("=" * 60)
    print("  CAMPUS IOT - MQTT BRIDGE")
    print("  Arduino Gateway <-> Mosquitto (Docker)")
    print("=" * 60)
    print()
    
    # Setup MQTT client
    client = mqtt.Client(client_id="campus_bridge", clean_session=CLEAN_SESSION)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Connect to Mosquitto (Docker)
    try:
        print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"[Error] Can't connect to MQTT broker: {e}")
        print()
        print("Make sure Docker is running:")
        print("  cd campus-iot && docker-compose up -d")
        print()
        sys.exit(1)
    
    # Connect to Arduino serial
    try:
        print(f"[Serial] Connecting to {SERIAL_PORT}...")
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        print(f"[Serial] Connected!")
        time.sleep(2)  # Wait for Arduino to reset
    except Exception as e:
        print(f"[Warning] Serial failed: {e}")
        print()
        print("Bridge will work in MQTT-only mode (no Arduino).")
        print("You can still test with terminal commands.")
        print()
        ser = None
    
    print()
    print("-" * 60)
    print("Bridge running! Press Ctrl+C to stop.")
    print("-" * 60)
    
    # Start threads
    if ser:
        t1 = threading.Thread(target=read_serial, args=(client,), daemon=True)
        t1.start()
    
    t2 = threading.Thread(target=read_terminal, args=(client,), daemon=True)
    t2.start()
    
    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if ser and ser.is_open:
            ser.close()
        client.loop_stop()
        client.disconnect()
        print("Done.")


if __name__ == "__main__":
    main()

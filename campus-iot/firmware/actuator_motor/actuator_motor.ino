#include <Servo.h>

#define xbeeSerial Serial1

Servo motor;

const int SERVO_PIN = 9;
const int LED_STATUS = 13;

// Motor limits
const int ANGLE_MIN = 0;
const int ANGLE_MAX = 180;
const int SPEED_STEP = 5;  // Degrees per step for smooth movement

// Current state
int currentAngle = 90;  // Start at middle position
int targetAngle = 90;
bool motorActive = false;

// Timing
const unsigned long STATUS_INTERVAL = 30000;  // Report status every 30s
const unsigned long MOVE_DELAY = 20;          // Delay between steps (smoothness)
unsigned long lastStatus = 0;
unsigned long lastMove = 0;

// Device identification
const char* DEVICE_ID = "motor_001";
const char* ROOM = "X101";
const char* BUILDING = "orion";

// What this motor controls
const char* MOTOR_TYPE = "ventilation";  // Options: ventilation, blinds, valve

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }
  
  xbeeSerial.begin(9600);
  
  motor.attach(SERVO_PIN);
  motor.write(currentAngle);
  
  pinMode(LED_STATUS, OUTPUT);
  
  Serial.println(F("========================================"));
  Serial.println(F("  Motor Actuator - Campus IoT"));
  Serial.print(F("  Room: "));
  Serial.println(ROOM);
  Serial.print(F("  Type: "));
  Serial.println(MOTOR_TYPE);
  Serial.println(F("========================================"));
  Serial.println(F("Commands via XBee:"));
  Serial.println(F("  CMD:motor:0-100  (percentage)"));
  Serial.println(F("  CMD:motor:open   (100%)"));
  Serial.println(F("  CMD:motor:close  (0%)"));
  Serial.println(F("  CMD:motor:toggle"));
  Serial.println(F("========================================"));
  Serial.println();
  
  // Send initial status
  sendStatus("startup");
}

void loop() {
  // Check for commands from XBee (forwarded by gateway)
  if (xbeeSerial.available()) {
    String incoming = xbeeSerial.readStringUntil('\n');
    incoming.trim();
    if (incoming.length() > 0) {
      processCommand(incoming, "XBee");
    }
  }
  
  // Also check USB serial for testing
  if (Serial.available()) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();
    if (incoming.length() > 0) {
      processCommand(incoming, "USB");
    }
  }
  
  // Smooth movement towards target
  if (currentAngle != targetAngle && millis() - lastMove >= MOVE_DELAY) {
    if (currentAngle < targetAngle) {
      currentAngle = min(currentAngle + SPEED_STEP, targetAngle);
    } else {
      currentAngle = max(currentAngle - SPEED_STEP, targetAngle);
    }
    motor.write(currentAngle);
    lastMove = millis();
    
    // LED indicates movement
    digitalWrite(LED_STATUS, HIGH);
    
    // Send status when movement completes
    if (currentAngle == targetAngle) {
      sendStatus("moved");
      digitalWrite(LED_STATUS, LOW);
    }
  }
  
  // Periodic status report
  if (millis() - lastStatus >= STATUS_INTERVAL) {
    sendStatus("heartbeat");
    lastStatus = millis();
  }
  
  delay(10);
}

void processCommand(String data, const char* source) {
  Serial.print(F("["));
  Serial.print(source);
  Serial.print(F("] Command: "));
  Serial.println(data);
  
  // Expected format: CMD:topic:value or just value for testing
  String command = data;
  
  // Extract value if CMD format
  if (data.startsWith("CMD:")) {
    int lastColon = data.lastIndexOf(':');
    if (lastColon > 4) {
      command = data.substring(lastColon + 1);
    }
  }
  
  command.toLowerCase();
  
  // Parse command
  if (command == "open" || command == "on") {
    setMotorPosition(100);
  }
  else if (command == "close" || command == "off") {
    setMotorPosition(0);
  }
  else if (command == "toggle") {
    int newPos = (currentAngle > 90) ? 0 : 100;
    setMotorPosition(newPos);
  }
  else if (command == "stop") {
    targetAngle = currentAngle;  // Stop where we are
    sendStatus("stopped");
  }
  else {
    // Try to parse as number (0-100 percentage)
    int value = command.toInt();
    if (value >= 0 && value <= 100) {
      setMotorPosition(value);
    } else {
      Serial.println(F("Unknown command. Use: 0-100, open, close, toggle"));
    }
  }
}

void setMotorPosition(int percentage) {
  // Convert percentage to angle
  targetAngle = map(percentage, 0, 100, ANGLE_MIN, ANGLE_MAX);
  motorActive = (percentage > 0);
  
  Serial.print(F("  -> Moving to "));
  Serial.print(percentage);
  Serial.print(F("% (angle: "));
  Serial.print(targetAngle);
  Serial.println(F(")"));
}

void sendStatus(const char* trigger) {
  // Calculate current percentage
  int percentage = map(currentAngle, ANGLE_MIN, ANGLE_MAX, 0, 100);
  
  // Build JSON message
  String message = "DATA:{";
  message += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  message += "\"actuator\":\"motor\",";
  message += "\"type\":\"" + String(MOTOR_TYPE) + "\",";
  message += "\"position\":" + String(percentage) + ",";
  message += "\"angle\":" + String(currentAngle) + ",";
  message += "\"target\":" + String(map(targetAngle, ANGLE_MIN, ANGLE_MAX, 0, 100)) + ",";
  message += "\"active\":" + String(motorActive ? "true" : "false") + ",";
  message += "\"trigger\":\"" + String(trigger) + "\",";
  message += "\"room\":\"" + String(ROOM) + "\",";
  message += "\"building\":\"" + String(BUILDING) + "\",";
  message += "\"timestamp\":" + String(millis() / 1000);
  message += "}";
  
  // Send via XBee
  xbeeSerial.println(message);
  
  // Debug output
  Serial.println(message);
  Serial.print(F("  -> Position: "));
  Serial.print(percentage);
  Serial.print(F("% | Active: "));
  Serial.println(motorActive ? "YES" : "NO");
  Serial.println();
  
  lastStatus = millis();
}

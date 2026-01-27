#define xbeeSerial Serial1

const int TRIG_PIN = 8;
const int ECHO_PIN = 9;
const int LED_PRESENCE = 13;

// Distance threshold in cm (anything closer = presence detected)
const int DISTANCE_THRESHOLD = 100;  // 1 meter

// Timing
const unsigned long DEBOUNCE_TIME = 2000;      // Ignore rapid changes
const unsigned long HEARTBEAT_INTERVAL = 60000; // Send status every minute
unsigned long lastDetection = 0;
unsigned long lastHeartbeat = 0;

// State
bool currentPresence = false;
bool previousPresence = false;

// Device identification - CHANGE THESE for each sensor
const char* DEVICE_ID = "sr04_001";
const char* ROOM = "X101";        // Room where this sensor is located
const char* BUILDING = "orion";   // Building name

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }
  
  xbeeSerial.begin(9600);
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PRESENCE, OUTPUT);
  
  Serial.println(F("========================================"));
  Serial.println(F("  HC-SR04 Presence Sensor - Campus IoT"));
  Serial.print(F("  Room: "));
  Serial.println(ROOM);
  Serial.println(F("========================================"));
  Serial.print(F("Distance threshold: "));
  Serial.print(DISTANCE_THRESHOLD);
  Serial.println(F(" cm"));
  Serial.println(F("Ready."));
  Serial.println(F("========================================"));
  Serial.println();
  
  // Send initial state
  sendPresenceState(false, "startup");
}

void loop() {
  long distance = measureDistance();
  
  // Presence detected if object closer than threshold
  currentPresence = (distance > 0 && distance < DISTANCE_THRESHOLD);
  
  // Send on state change (with debounce to avoid noise)
  if (currentPresence != previousPresence) {
    if (millis() - lastDetection > DEBOUNCE_TIME) {
      sendPresenceState(currentPresence, "detection");
      previousPresence = currentPresence;
      lastDetection = millis();
    }
  }
  
  // Heartbeat - send current state periodically
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    sendPresenceState(currentPresence, "heartbeat");
    lastHeartbeat = millis();
  }
  
  // LED indicates presence
  digitalWrite(LED_PRESENCE, currentPresence ? HIGH : LOW);
  delay(100);
}

long measureDistance() {
  // Send ultrasonic pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read echo (timeout after 30ms = ~5m max)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  
  // Calculate distance
  // Speed of sound = 340 m/s = 0.034 cm/us
  // Distance = (duration / 2) * 0.034
  long distance = duration * 0.034 / 2;
  
  return distance;
}

void sendPresenceState(bool presence, const char* trigger) {
  // Build JSON message for gateway
  String message = "DATA:{";
  message += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  message += "\"sensor\":\"presence\",";
  message += "\"detected\":" + String(presence ? "true" : "false") + ",";
  message += "\"trigger\":\"" + String(trigger) + "\",";
  message += "\"room\":\"" + String(ROOM) + "\",";
  message += "\"building\":\"" + String(BUILDING) + "\",";
  message += "\"timestamp\":" + String(millis() / 1000);
  message += "}";
  
  // Send via XBee to gateway
  xbeeSerial.println(message);
  
  // Also print to USB serial for debugging
  Serial.println(message);
  Serial.print(F("  -> Presence: "));
  Serial.print(presence ? F("YES") : F("NO"));
  Serial.print(F(" ("));
  Serial.print(trigger);
  Serial.println(F(")"));
  Serial.println();
}

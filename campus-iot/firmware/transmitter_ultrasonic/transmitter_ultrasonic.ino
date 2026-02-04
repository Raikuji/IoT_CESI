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

// Energy saving settings (updated via MQTT commands)
bool energyEnabled = false;
unsigned long energyIntervalSec = 120;
unsigned long energyIntervalNightSec = 300;
String energyProfile = "normal";

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
  handleCommands();

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
  unsigned long heartbeatInterval = HEARTBEAT_INTERVAL;
  if (energyEnabled) {
    heartbeatInterval = (energyProfile == "night" ? energyIntervalNightSec : energyIntervalSec) * 1000UL;
  }
  if (millis() - lastHeartbeat > heartbeatInterval) {
    sendPresenceState(currentPresence, "heartbeat");
    lastHeartbeat = millis();
  }
  
  // LED indicates presence
  digitalWrite(LED_PRESENCE, currentPresence ? HIGH : LOW);
  delay(100);
}

void handleCommands() {
  if (xbeeSerial.available()) {
    String line = xbeeSerial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("CMD:")) {
      applyEnergyCommand(line);
    }
  }
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("CMD:")) {
      applyEnergyCommand(line);
    }
  }
}

void applyEnergyCommand(String cmd) {
  int first = cmd.indexOf(':');
  int second = cmd.indexOf(':', first + 1);
  if (second < 0) return;

  String topic = cmd.substring(first + 1, second);
  String payload = cmd.substring(second + 1);

  int idx = topic.indexOf("/controls/energy/");
  if (idx < 0) return;
  String rest = topic.substring(idx + 17);
  int slash = rest.indexOf('/');
  if (slash < 0) return;
  String room = rest.substring(0, slash);
  String sensorType = rest.substring(slash + 1);

  if (room != ROOM) return;
  if (sensorType != "presence") return;

  energyEnabled = jsonBool(payload, "enabled", energyEnabled);
  energyIntervalSec = jsonInt(payload, "refresh_interval", energyIntervalSec);
  energyIntervalNightSec = jsonInt(payload, "refresh_interval_night", energyIntervalNightSec);
  energyProfile = jsonString(payload, "profile", energyProfile);

  Serial.print(F("[ENERGY] enabled="));
  Serial.print(energyEnabled ? "true" : "false");
  Serial.print(F(" interval="));
  Serial.print(energyIntervalSec);
  Serial.print(F(" night="));
  Serial.print(energyIntervalNightSec);
  Serial.print(F(" profile="));
  Serial.println(energyProfile);
}

bool jsonBool(String json, String key, bool defVal) {
  String needle = "\"" + key + "\":";
  int idx = json.indexOf(needle);
  if (idx < 0) return defVal;
  int start = idx + needle.length();
  String value = json.substring(start);
  value.trim();
  if (value.startsWith("true")) return true;
  if (value.startsWith("false")) return false;
  return defVal;
}

unsigned long jsonInt(String json, String key, unsigned long defVal) {
  String needle = "\"" + key + "\":";
  int idx = json.indexOf(needle);
  if (idx < 0) return defVal;
  int start = idx + needle.length();
  int end = start;
  while (end < json.length() && isDigit(json[end])) end++;
  if (end == start) return defVal;
  return (unsigned long) json.substring(start, end).toInt();
}

String jsonString(String json, String key, String defVal) {
  String needle = "\"" + key + "\":\"";
  int idx = json.indexOf(needle);
  if (idx < 0) return defVal;
  int start = idx + needle.length();
  int end = json.indexOf("\"", start);
  if (end < 0) return defVal;
  return json.substring(start, end);
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

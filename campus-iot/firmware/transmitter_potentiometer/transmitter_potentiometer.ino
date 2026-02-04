#define xbeeSerial Serial1

const int POT_PIN = A0;
const int LED_STATUS = 13;

// Timing
const unsigned long SEND_INTERVAL = 5000;  // Send every 5 seconds
const int CHANGE_THRESHOLD = 20;           // Min change to trigger immediate send
unsigned long lastSend = 0;
int lastValue = 0;

// Energy saving settings (updated via MQTT commands)
bool energyEnabled = false;
unsigned long energyIntervalSec = 120;
unsigned long energyIntervalNightSec = 300;
String energyProfile = "normal";

// Device identification - CHANGE THESE for each sensor
const char* DEVICE_ID = "pot_001";
const char* ROOM = "X101";
const char* BUILDING = "orion";

// What this potentiometer controls (for display in app)
// Options: "light", "dimmer", "level", "adjustment"
const char* POT_TYPE = "light";

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }
  
  xbeeSerial.begin(9600);
  pinMode(LED_STATUS, OUTPUT);
  
  Serial.println(F("========================================"));
  Serial.println(F("  Potentiometer Sensor - Campus IoT"));
  Serial.print(F("  Room: "));
  Serial.println(ROOM);
  Serial.print(F("  Type: "));
  Serial.println(POT_TYPE);
  Serial.println(F("========================================"));
  Serial.println();
  
  // Send initial value
  int initialValue = analogRead(POT_PIN);
  sendData(initialValue, "startup");
  lastValue = initialValue;
}

void loop() {
  handleCommands();

  int currentValue = analogRead(POT_PIN);
  
  // Convert to percentage (0-100)
  int percentage = map(currentValue, 0, 1023, 0, 100);
  int lastPercentage = map(lastValue, 0, 1023, 0, 100);
  
  bool significantChange = abs(currentValue - lastValue) > CHANGE_THRESHOLD;
  unsigned long interval = SEND_INTERVAL;
  if (energyEnabled) {
    interval = (energyProfile == "night" ? energyIntervalNightSec : energyIntervalSec) * 1000UL;
  }
  bool timeToSend = (millis() - lastSend) >= interval;
  
  if (significantChange || timeToSend) {
    sendData(currentValue, significantChange ? "change" : "periodic");
    lastValue = currentValue;
    lastSend = millis();
  }
  
  // LED brightness reflects potentiometer value
  analogWrite(LED_STATUS, percentage * 2.55);  // 0-255
  
  delay(50);
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
  if (sensorType != String(POT_TYPE)) return;

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

void sendData(int rawValue, const char* trigger) {
  // Convert to percentage
  int percentage = map(rawValue, 0, 1023, 0, 100);
  
  // Build JSON message
  String message = "DATA:{";
  message += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  message += "\"sensor\":\"potentiometer\",";
  message += "\"type\":\"" + String(POT_TYPE) + "\",";
  message += "\"raw\":" + String(rawValue) + ",";
  message += "\"value\":" + String(percentage) + ",";
  message += "\"trigger\":\"" + String(trigger) + "\",";
  message += "\"room\":\"" + String(ROOM) + "\",";
  message += "\"building\":\"" + String(BUILDING) + "\",";
  message += "\"timestamp\":" + String(millis() / 1000);
  message += "}";
  
  // Send via XBee
  xbeeSerial.println(message);
  
  // Debug output
  Serial.println(message);
  Serial.print(F("  -> Level: "));
  Serial.print(percentage);
  Serial.print(F("% (raw: "));
  Serial.print(rawValue);
  Serial.println(F(")"));
  Serial.println();
}

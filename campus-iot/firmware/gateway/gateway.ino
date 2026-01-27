#define xbeeSerial Serial1

const int LED_RX = 13;  // blinks when we receive data

// stats to see if everything works
unsigned long messagesReceived = 0;
unsigned long errors = 0;
unsigned long lastStats = 0;
const unsigned long STATS_INTERVAL = 60000;  // print stats every 60s

// Room configuration - CHANGE THIS based on where your gateway is
const char* ROOM = "X101";
const char* BUILDING = "orion";

void setup() {
  // USB serial for Python bridge (and debug)
  Serial.begin(9600);
  while (!Serial) { ; }  // wait for USB on R4
  
  // XBee serial
  xbeeSerial.begin(9600);
  pinMode(LED_RX, OUTPUT);
  
  Serial.println(F("========================================"));
  Serial.println(F("  ZigBee Gateway - Campus IoT"));
  Serial.print(F("  Room: "));
  Serial.println(ROOM);
  Serial.println(F("========================================"));
  Serial.println(F("Waiting for sensor data..."));
  Serial.println(F("(You can type DATA:{...} to test)"));
  Serial.println();
}

void loop() {
  // check if XBee sent something
  if (xbeeSerial.available()) {
    String incomingData = xbeeSerial.readStringUntil('\n');
    incomingData.trim();
    if (incomingData.length() > 0) {
      processIncoming(incomingData, "XBee");
    }
  }
  
  // also check USB serial (useful for testing without XBee)
  if (Serial.available()) {
    String incomingData = Serial.readStringUntil('\n');
    incomingData.trim();
    if (incomingData.length() > 0) {
      processIncoming(incomingData, "USB");
    }
  }
  
  // print stats periodically so we know it's alive
  if (millis() - lastStats > STATS_INTERVAL) {
    printStats();
    lastStats = millis();
  }
}

void processIncoming(String data, const char* source) {
  digitalWrite(LED_RX, HIGH);  // visual feedback
  
  // log what we got
  Serial.print(F("["));
  Serial.print(source);
  Serial.print(F("] Received: "));
  Serial.println(data);
  
  // DATA: prefix = sensor data, we need to forward to MQTT
  if (data.startsWith("DATA:")) {
    processSensorData(data);
    messagesReceived++;
  } 
  // CMD: prefix = command from MQTT (for actuators)
  else if (data.startsWith("CMD:")) {
    processCommand(data);
  } 
  else {
    // unknown format, log it for debug
    Serial.println(F("DEBUG: Unknown format"));
    errors++;
  }
  
  delay(50);
  digitalWrite(LED_RX, LOW);
}

void processSensorData(String data) {
  // extract JSON part (everything after "DATA:")
  String jsonData = data.substring(5);
  
  // parse JSON to extract values and determine topic
  parseAndPublish(jsonData);
}

void parseAndPublish(String jsonData) {
  // Extract room from JSON if present, otherwise use gateway's default room
  String room = extractString(jsonData, "room");
  if (room.length() == 0) room = ROOM;
  
  // Base topics for web app
  String sensorTopic = "campus/" + String(BUILDING) + "/" + room + "/sensors/";
  String actuatorTopic = "campus/" + String(BUILDING) + "/" + room + "/actuators/";
  
  // ==================== SENSORS ====================
  
  // BME280 - Temperature & Humidity sensor
  if (jsonData.indexOf("\"sensor\":\"bme280\"") > 0 || jsonData.indexOf("\"sensor\":\"climate\"") > 0) {
    float temp = extractFloat(jsonData, "temperature");
    float hum = extractFloat(jsonData, "humidity");
    
    // Publish temperature
    Serial.print(F("MQTT:"));
    Serial.print(sensorTopic + "temperature");
    Serial.print(F(":"));
    Serial.println(temp);
    
    // Publish humidity
    Serial.print(F("MQTT:"));
    Serial.print(sensorTopic + "humidity");
    Serial.print(F(":"));
    Serial.println(hum);
  }
  
  // HC-SR04 - Presence sensor
  else if (jsonData.indexOf("\"sensor\":\"presence\"") > 0) {
    bool detected = jsonData.indexOf("\"detected\":true") > 0;
    
    Serial.print(F("MQTT:"));
    Serial.print(sensorTopic + "presence");
    Serial.print(F(":"));
    Serial.println(detected ? "1" : "0");
  }
  
  // Potentiometer - Light/Level sensor
  else if (jsonData.indexOf("\"sensor\":\"potentiometer\"") > 0) {
    int value = extractInt(jsonData, "value");
    String potType = extractString(jsonData, "type");
    if (potType.length() == 0) potType = "light";
    
    Serial.print(F("MQTT:"));
    Serial.print(sensorTopic + potType);
    Serial.print(F(":"));
    Serial.println(value);
  }
  
  // ==================== ACTUATORS ====================
  
  // Motor actuator status
  else if (jsonData.indexOf("\"actuator\":\"motor\"") > 0) {
    int position = extractInt(jsonData, "position");
    bool active = jsonData.indexOf("\"active\":true") > 0;
    
    // Publish position
    Serial.print(F("MQTT:"));
    Serial.print(actuatorTopic + "motor/position");
    Serial.print(F(":"));
    Serial.println(position);
    
    // Publish active state
    Serial.print(F("MQTT:"));
    Serial.print(actuatorTopic + "motor/active");
    Serial.print(F(":"));
    Serial.println(active ? "1" : "0");
  }
  
  // Speaker actuator status
  else if (jsonData.indexOf("\"actuator\":\"speaker\"") > 0) {
    bool active = jsonData.indexOf("\"active\":true") > 0;
    String alertType = extractString(jsonData, "alert_type");
    
    Serial.print(F("MQTT:"));
    Serial.print(actuatorTopic + "speaker/active");
    Serial.print(F(":"));
    Serial.println(active ? "1" : "0");
    
    Serial.print(F("MQTT:"));
    Serial.print(actuatorTopic + "speaker/alert");
    Serial.print(F(":"));
    Serial.println(alertType);
  }
  
  // Unknown - publish raw JSON
  else {
    Serial.print(F("MQTT:"));
    Serial.print(sensorTopic + "unknown");
    Serial.print(F(":"));
    Serial.println(jsonData);
  }
}

float extractFloat(String json, String key) {
  // Simple JSON float extraction
  String searchKey = "\"" + key + "\":";
  int startIndex = json.indexOf(searchKey);
  if (startIndex < 0) return 0;
  
  startIndex += searchKey.length();
  int endIndex = json.indexOf(",", startIndex);
  if (endIndex < 0) endIndex = json.indexOf("}", startIndex);
  
  String valueStr = json.substring(startIndex, endIndex);
  return valueStr.toFloat();
}

int extractInt(String json, String key) {
  return (int)extractFloat(json, key);
}

String extractString(String json, String key) {
  // Extract string value from JSON
  String searchKey = "\"" + key + "\":\"";
  int startIndex = json.indexOf(searchKey);
  if (startIndex < 0) return "";
  
  startIndex += searchKey.length();
  int endIndex = json.indexOf("\"", startIndex);
  if (endIndex < 0) return "";
  
  return json.substring(startIndex, endIndex);
}

void processCommand(String data) {
  // commands come from MQTT via Python bridge
  // format: CMD:topic:payload
  Serial.print(F("[CMD] "));
  Serial.println(data);
  
  // Forward to XBee for actuators if needed
  xbeeSerial.println(data);
}

void printStats() {
  Serial.println(F("--- GATEWAY STATS ---"));
  Serial.print(F("Room: "));
  Serial.println(ROOM);
  Serial.print(F("Messages: "));
  Serial.println(messagesReceived);
  Serial.print(F("Errors: "));
  Serial.println(errors);
  Serial.print(F("Uptime: "));
  Serial.print(millis() / 1000);
  Serial.println(F("s"));
  Serial.println();
}

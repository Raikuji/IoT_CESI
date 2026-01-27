#define xbeeSerial Serial1

const int POT_PIN = A0;
const int LED_STATUS = 13;

// Timing
const unsigned long SEND_INTERVAL = 5000;  // Send every 5 seconds
const int CHANGE_THRESHOLD = 20;           // Min change to trigger immediate send
unsigned long lastSend = 0;
int lastValue = 0;

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
  int currentValue = analogRead(POT_PIN);
  
  // Convert to percentage (0-100)
  int percentage = map(currentValue, 0, 1023, 0, 100);
  int lastPercentage = map(lastValue, 0, 1023, 0, 100);
  
  bool significantChange = abs(currentValue - lastValue) > CHANGE_THRESHOLD;
  bool timeToSend = (millis() - lastSend) >= SEND_INTERVAL;
  
  if (significantChange || timeToSend) {
    sendData(currentValue, significantChange ? "change" : "periodic");
    lastValue = currentValue;
    lastSend = millis();
  }
  
  // LED brightness reflects potentiometer value
  analogWrite(LED_STATUS, percentage * 2.55);  // 0-255
  
  delay(50);
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

#define xbeeSerial Serial1

const int SPEAKER_PIN = 10;
const int LED_STATUS = 13;

// Sound frequencies (Hz)
const int FREQ_LOW = 440;      // A4 - Warning
const int FREQ_MED = 880;      // A5 - Alert
const int FREQ_HIGH = 1760;    // A6 - Danger
const int FREQ_BEEP = 1000;    // Standard beep

// Alert patterns
enum AlertType {
  ALERT_NONE,
  ALERT_INFO,      // Single beep
  ALERT_WARNING,   // Double beep
  ALERT_DANGER,    // Continuous alarm
  ALERT_CO2,       // Special CO2 pattern
  ALERT_SUCCESS    // Happy sound
};

// Current state
AlertType currentAlert = ALERT_NONE;
bool alertActive = false;
unsigned long alertStartTime = 0;
const unsigned long ALERT_DURATION = 5000;  // Auto-stop after 5 seconds

// Timing
const unsigned long STATUS_INTERVAL = 60000;
unsigned long lastStatus = 0;

// Device identification
const char* DEVICE_ID = "speaker_001";
const char* ROOM = "X101";
const char* BUILDING = "orion";

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }
  
  xbeeSerial.begin(9600);
  
  pinMode(SPEAKER_PIN, OUTPUT);
  pinMode(LED_STATUS, OUTPUT);
  
  Serial.println(F("========================================"));
  Serial.println(F("  Speaker Actuator - Campus IoT"));
  Serial.print(F("  Room: "));
  Serial.println(ROOM);
  Serial.println(F("========================================"));
  Serial.println(F("Commands via XBee:"));
  Serial.println(F("  CMD:speaker:beep     (single beep)"));
  Serial.println(F("  CMD:speaker:warning  (double beep)"));
  Serial.println(F("  CMD:speaker:danger   (alarm)"));
  Serial.println(F("  CMD:speaker:co2      (CO2 alert)"));
  Serial.println(F("  CMD:speaker:success  (happy sound)"));
  Serial.println(F("  CMD:speaker:stop     (silence)"));
  Serial.println(F("  CMD:speaker:test     (test all)"));
  Serial.println(F("========================================"));
  Serial.println();
  
  // Startup beep
  playBeep(FREQ_BEEP, 100);
  delay(100);
  playBeep(FREQ_HIGH, 100);
  
  sendStatus("startup");
}

void loop() {
  // Check for commands from XBee
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
  
  // Play current alert pattern
  if (alertActive) {
    playAlertPattern();
    
    // Auto-stop after duration
    if (millis() - alertStartTime > ALERT_DURATION) {
      stopAlert();
    }
  }
  
  // Periodic status
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
  
  // Extract command value
  String command = data;
  if (data.startsWith("CMD:")) {
    int lastColon = data.lastIndexOf(':');
    if (lastColon > 4) {
      command = data.substring(lastColon + 1);
    }
  }
  
  command.toLowerCase();
  
  // Parse command
  if (command == "beep" || command == "info") {
    startAlert(ALERT_INFO);
  }
  else if (command == "warning" || command == "warn") {
    startAlert(ALERT_WARNING);
  }
  else if (command == "danger" || command == "alarm") {
    startAlert(ALERT_DANGER);
  }
  else if (command == "co2") {
    startAlert(ALERT_CO2);
  }
  else if (command == "success" || command == "ok") {
    startAlert(ALERT_SUCCESS);
  }
  else if (command == "stop" || command == "off" || command == "silence") {
    stopAlert();
  }
  else if (command == "test") {
    testAllSounds();
  }
  else {
    // Try to parse as frequency
    int freq = command.toInt();
    if (freq >= 100 && freq <= 5000) {
      playBeep(freq, 500);
    } else {
      Serial.println(F("Unknown command"));
    }
  }
}

void startAlert(AlertType type) {
  currentAlert = type;
  alertActive = true;
  alertStartTime = millis();
  digitalWrite(LED_STATUS, HIGH);
  
  Serial.print(F("  -> Alert started: "));
  Serial.println(getAlertName(type));
  
  sendStatus("alert_start");
}

void stopAlert() {
  currentAlert = ALERT_NONE;
  alertActive = false;
  noTone(SPEAKER_PIN);
  digitalWrite(LED_STATUS, LOW);
  
  Serial.println(F("  -> Alert stopped"));
  
  sendStatus("alert_stop");
}

void playAlertPattern() {
  unsigned long elapsed = millis() - alertStartTime;
  
  switch (currentAlert) {
    case ALERT_INFO:
      // Single beep
      if (elapsed < 200) {
        tone(SPEAKER_PIN, FREQ_BEEP);
      } else {
        noTone(SPEAKER_PIN);
        alertActive = false;
      }
      break;
      
    case ALERT_WARNING:
      // Double beep pattern
      if (elapsed < 150) {
        tone(SPEAKER_PIN, FREQ_MED);
      } else if (elapsed < 250) {
        noTone(SPEAKER_PIN);
      } else if (elapsed < 400) {
        tone(SPEAKER_PIN, FREQ_MED);
      } else if (elapsed < 1000) {
        noTone(SPEAKER_PIN);
      } else {
        alertStartTime = millis();  // Repeat
      }
      break;
      
    case ALERT_DANGER:
      // Continuous alternating alarm
      if ((elapsed / 200) % 2 == 0) {
        tone(SPEAKER_PIN, FREQ_HIGH);
      } else {
        tone(SPEAKER_PIN, FREQ_LOW);
      }
      break;
      
    case ALERT_CO2:
      // Special CO2 pattern: 3 short beeps, pause, repeat
      {
        int phase = (elapsed / 100) % 10;
        if (phase < 1 || (phase >= 2 && phase < 3) || (phase >= 4 && phase < 5)) {
          tone(SPEAKER_PIN, FREQ_MED);
        } else {
          noTone(SPEAKER_PIN);
        }
      }
      break;
      
    case ALERT_SUCCESS:
      // Happy ascending tones
      if (elapsed < 100) {
        tone(SPEAKER_PIN, 523);  // C5
      } else if (elapsed < 200) {
        tone(SPEAKER_PIN, 659);  // E5
      } else if (elapsed < 400) {
        tone(SPEAKER_PIN, 784);  // G5
      } else {
        noTone(SPEAKER_PIN);
        alertActive = false;
      }
      break;
      
    default:
      noTone(SPEAKER_PIN);
      break;
  }
}

void playBeep(int frequency, int duration) {
  tone(SPEAKER_PIN, frequency, duration);
  delay(duration);
  noTone(SPEAKER_PIN);
}

void testAllSounds() {
  Serial.println(F("Testing all sounds..."));
  
  Serial.println(F("  1. Info beep"));
  playBeep(FREQ_BEEP, 200);
  delay(500);
  
  Serial.println(F("  2. Warning"));
  playBeep(FREQ_MED, 150);
  delay(100);
  playBeep(FREQ_MED, 150);
  delay(500);
  
  Serial.println(F("  3. Danger"));
  for (int i = 0; i < 3; i++) {
    playBeep(FREQ_HIGH, 100);
    playBeep(FREQ_LOW, 100);
  }
  delay(500);
  
  Serial.println(F("  4. Success"));
  playBeep(523, 100);
  playBeep(659, 100);
  playBeep(784, 200);
  
  Serial.println(F("Test complete!"));
}

const char* getAlertName(AlertType type) {
  switch (type) {
    case ALERT_INFO: return "INFO";
    case ALERT_WARNING: return "WARNING";
    case ALERT_DANGER: return "DANGER";
    case ALERT_CO2: return "CO2";
    case ALERT_SUCCESS: return "SUCCESS";
    default: return "NONE";
  }
}

void sendStatus(const char* trigger) {
  String message = "DATA:{";
  message += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  message += "\"actuator\":\"speaker\",";
  message += "\"active\":" + String(alertActive ? "true" : "false") + ",";
  message += "\"alert_type\":\"" + String(getAlertName(currentAlert)) + "\",";
  message += "\"trigger\":\"" + String(trigger) + "\",";
  message += "\"room\":\"" + String(ROOM) + "\",";
  message += "\"building\":\"" + String(BUILDING) + "\",";
  message += "\"timestamp\":" + String(millis() / 1000);
  message += "}";
  
  xbeeSerial.println(message);
  Serial.println(message);
  Serial.println();
  
  lastStatus = millis();
}

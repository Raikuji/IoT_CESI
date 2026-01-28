#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include "../lib/hmac_security.h"

#define xbeeSerial Serial1

Adafruit_BME280 bme;

const int LED_STATUS = 13;

// Timing - sends more frequently if out of comfort range
const unsigned long INTERVAL_NORMAL = 60000;   // 1 minute normally
const unsigned long INTERVAL_FAST = 30000;     // 30 sec if uncomfortable
unsigned long lastSend = 0;

// Comfort thresholds
const float TEMP_MIN = 19.0;
const float TEMP_MAX = 23.0;
const float HUM_MIN = 40.0;
const float HUM_MAX = 60.0;

// Device identification - CHANGE THESE for each sensor
const char* DEVICE_ID = "bme280_001";
const char* ROOM = "X101";        // Room where this sensor is located
const char* BUILDING = "orion";   // Building name

// Security - HMAC signature (same key as backend!)
const char* HMAC_SECRET = "campus-orion-iot-secret-2024";
HMACSecurity hmac(HMAC_SECRET);

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }
  
  xbeeSerial.begin(9600);
  pinMode(LED_STATUS, OUTPUT);
  
  Serial.println(F("========================================"));
  Serial.println(F("  BME280 Sensor - Campus IoT"));
  Serial.print(F("  Room: "));
  Serial.println(ROOM);
  Serial.println(F("========================================"));
  
  // Initialize BME280 - try both common addresses
  if (!bme.begin(0x76)) {
    Serial.println(F("BME280 not found at 0x76, trying 0x77..."));
    if (!bme.begin(0x77)) {
      Serial.println(F("BME280 not found! Check wiring:"));
      Serial.println(F("  VCC -> 3.3V"));
      Serial.println(F("  GND -> GND"));
      Serial.println(F("  SDA -> A4"));
      Serial.println(F("  SCL -> A5"));
      // Blink LED to indicate error
      while (1) {
        digitalWrite(LED_STATUS, (millis() / 500) % 2);
        delay(100);
      }
    }
  }
  
  Serial.println(F("BME280 initialized!"));
  Serial.println(F("Reading: Temperature, Humidity"));
  Serial.println(F("========================================"));
  Serial.println();
  
  delay(100);
}

void loop() {
  float temperature = bme.readTemperature();
  float humidity = bme.readHumidity();
  
  // Check if out of comfort range
  bool outOfRange = (temperature < TEMP_MIN || temperature > TEMP_MAX ||
                     humidity < HUM_MIN || humidity > HUM_MAX);
  
  // Send faster if uncomfortable
  unsigned long interval = outOfRange ? INTERVAL_FAST : INTERVAL_NORMAL;
  
  if (millis() - lastSend >= interval) {
    sendData(temperature, humidity, outOfRange);
    lastSend = millis();
  }
  
  // LED indicates comfort status
  digitalWrite(LED_STATUS, outOfRange ? HIGH : LOW);
  delay(100);
}

void sendData(float temp, float hum, bool outOfRange) {
  // Determine comfort status
  String comfort = "optimal";
  if (outOfRange) {
    if (temp < TEMP_MIN) comfort = "cold";
    else if (temp > TEMP_MAX) comfort = "hot";
    else if (hum < HUM_MIN) comfort = "dry";
    else if (hum > HUM_MAX) comfort = "humid";
  }
  
  unsigned long timestamp = millis();
  
  // Send temperature with HMAC signature
  String tempSigned = hmac.signSensorData("temperature", temp, timestamp);
  String tempMsg = "SECURE:" + tempSigned;
  xbeeSerial.println(tempMsg);
  Serial.println(tempMsg);
  
  // Send humidity with HMAC signature
  String humSigned = hmac.signSensorData("humidity", hum, timestamp);
  String humMsg = "SECURE:" + humSigned;
  xbeeSerial.println(humMsg);
  Serial.println(humMsg);
  
  // Also send full JSON for backward compatibility
  String message = "DATA:{";
  message += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  message += "\"sensor\":\"bme280\",";
  message += "\"temperature\":" + String(temp, 1) + ",";
  message += "\"humidity\":" + String(hum, 1) + ",";
  message += "\"comfort\":\"" + comfort + "\",";
  message += "\"room\":\"" + String(ROOM) + "\",";
  message += "\"building\":\"" + String(BUILDING) + "\",";
  message += "\"timestamp\":" + String(timestamp / 1000);
  message += "}";
  
  xbeeSerial.println(message);
  
  Serial.print(F("  -> "));
  Serial.print(temp, 1);
  Serial.print(F(" C | "));
  Serial.print(hum, 1);
  Serial.print(F(" % | "));
  Serial.print(comfort);
  Serial.println(F(" [SIGNED]"));
  Serial.println();
}

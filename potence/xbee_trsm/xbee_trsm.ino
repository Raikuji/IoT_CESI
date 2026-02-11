/**
 * Project: IoT Sensor Node (FIXED for Offline SSL)
 * Board: Arduino UNO R4 WiFi
 */

#include <SoftwareSerial.h>
#include <Wire.h>
#include <WiFiS3.h>
#include <WiFiSSLClient.h>
#include <PubSubClient.h>
#include <SHA256.h>

// ==========================================
//              PIN DEFINITIONS
// ==========================================
const int PIN_XBEE_RX = 2;
const int PIN_XBEE_TX = 3;
const int PIN_ULTRASONIC_TRIG = 4;
const int PIN_ULTRASONIC_ECHO = 5;
const int PIN_ANALOG_CO2 = A0;   
const int PIN_ANALOG_BTN = A1;    

// ==========================================
//           HMAC CONFIGURATION
// ==========================================
const char* hmacSecretKeyPrefix = "campus-orion-iot-secret-%s"; 
char hmacSecretKey[29];
const int HMAC_SIZE = 32;

// ==========================================
//           BME280 CONFIGURATION
// ==========================================
#define BME280_ADDR      0x76    
#define REG_ID           0xD0
#define REG_HUM_MSB      0xFD
#define REG_CTRL_HUM     0xF2
#define REG_CTRL_MEAS    0xF4
#define REG_CONFIG       0xF5
#define REG_CALIB_DIG_T1 0x88
#define REG_CALIB_DIG_H1 0xA1
#define REG_CALIB_DIG_H2 0xE1

const int activeTime = 6000;
const int sleepTime = 60000;
int loopTime = activeTime;
int counterEmpty = 0;

// ==========================================
//           NETWORK & MQTT SETTINGS
// ==========================================
const char ssid[] = "CESI_Iot";
const char pass[] = "#RO_i0t.n3t";

const char* mqtt_server = "169.254.46.215"; 
const int mqtt_port = 1883;
const char* mqtt_client_id = "Groupe3_IoT";

// Topics
const char* topic_pub_temp = "campus/orion/sensors/temperature";
const char* topic_pub_humi = "campus/orion/sensors/humidity";
const char* topic_pub_pres = "campus/orion/sensors/presence";
const char* topic_pub_co2  = "campus/orion/sensors/co2";

const char* topic_sub_heat = "campus/orion/actuators/heating/setpoint";

// Static IP Configuration (For Link-Local Network)
IPAddress local_IP(169, 254, 46, 14);
IPAddress gateway(169, 254, 46, 215); // Gateway points to broker PC
IPAddress subnet(255, 255, 0, 0);
IPAddress dns(169, 254, 46, 215);

// Root CA (Must match your ca.crt file)
const char root_ca[] =
"-----BEGIN CERTIFICATE-----\n" \
"MIIEBzCCAu+gAwIBAgIUdKjSk+9KWYqvDN6AxQ3TDJ3Dk+cwDQYJKoZIhvcNAQEL\n" \
"BQAwgZIxCzAJBgNVBAYTAkZSMRswGQYDVQQIDBJNZXVydGhlLWV0LU1vc2VsbGUx\n" \
"DjAMBgNVBAcMBU5hbmN5MQ0wCwYDVQQKDARjZXNpMQ0wCwYDVQQLDARncnAzMRAw\n" \
"DgYDVQQDDAdBbnRvaW5lMSYwJAYJKoZIhvcNAQkBFhdhbnRvaW5lLmdjaG50QGdt\n" \
"YWlsLmNvbTAeFw0yNjAyMTAxMjI2MjJaFw0zNjAyMDgxMjI2MjJaMIGSMQswCQYD\n" \
"VQQGEwJGUjEbMBkGA1UECAwSTWV1cnRoZS1ldC1Nb3NlbGxlMQ4wDAYDVQQHDAVO\n" \
"YW5jeTENMAsGA1UECgwEY2VzaTENMAsGA1UECwwEZ3JwMzEQMA4GA1UEAwwHQW50\n" \
"b2luZTEmMCQGCSqGSIb3DQEJARYXYW50b2luZS5nY2hudEBnbWFpbC5jb20wggEi\n" \
"MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDJcwZ/Nxh+QV8EBjb0XGOEyDyn\n" \
"olhM2o+dgmJUn0BLrgQXF616fOs8AxLg+iDVm0B2RIuKUGXmSIb9o9r2b95+LT1I\n" \
"H780PfnKHLRYyLnAZ2Mtw066JQoe3tWFxGmxloLFUtUT0pHtR8KF8+oF31QuuvA3\n" \
"v/oGpb1NIqnuFqP9LyJ5gnwMSgM5HWFxYRR1DBhy6Md8Kubcn2nBeVe1WItOCHkA\n" \
"CfKZSYP7rfLHps8K7IiL6i6yUCtC1YwbHoZxgU6cnxkWISOyzHW7kizJJNOp0Q/r\n" \
"luEPE6Uvcf5qVnRhq4yY/OTWcjTJGXRA88pGdfkszSKQyZL3Q0mh6bAe/R6ZAgMB\n" \
"AAGjUzBRMB0GA1UdDgQWBBQXhram6zXO+S7O721OlHPZljS1HzAfBgNVHSMEGDAW\n" \
"gBQXhram6zXO+S7O721OlHPZljS1HzAPBgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3\n" \
"DQEBCwUAA4IBAQBYON/xK6X5cD9n3+ujrXJ22I3eyduf4vliKFW1gQ63Jp/IOLEq\n" \
"dS14v7GC5ooLrudZW0eBYZW/irwkitmRk/ymQrjBHEe8wuzwuPJ2cZ2m73aSB/uj\n" \
"Rb1P7yhe0R+me/BMmq7cogssTUtrfEps81KzjGOOQdTI8FnGpaVSPbXT9MWZHkCK\n" \
"7Y5WMBQA6DnP2wIvlQsZSGsRcwBHyYjDR6MOdNeWmdMB15e779F+sJu2MYZ1u8SO\n" \
"vfAGADXC833v+6DU3iv7UiX14s5YDfnjoFlmjyEtDANbFkaC1C2mZiH0R4facR3X\n" \
"LlZXZfmWyeqU9ThY/VzWtf8C2NJxkPok/UC9\n" \
"-----END CERTIFICATE-----\n";

// ==========================================
//              GLOBAL OBJECTS
// ==========================================
SoftwareSerial xbeeSerial(PIN_XBEE_RX, PIN_XBEE_TX);
WiFiSSLClient sslClient;
WiFiClient wifiClient;
PubSubClient client(wifiClient);

// BME280 Global Variables
uint16_t dig_T1;
int16_t  dig_T2, dig_T3;
uint8_t  dig_H1, dig_H3;
int16_t  dig_H2, dig_H4, dig_H5;
int8_t   dig_H6;
int32_t  t_fine; 
char currentRoom[10] = "X003";

// ==========================================
//               SETUP
// ==========================================
void setup() {
    Serial.begin(9600);
    xbeeSerial.begin(9600);
    Wire.begin();

    pinMode(PIN_ULTRASONIC_TRIG, OUTPUT);
    pinMode(PIN_ULTRASONIC_ECHO, INPUT);

    Serial.println("Initializing BME280...");
    readCalibrationData();

    // 1. Initialize Network
    setupWiFi();

    // 3. Load Certificate
    Serial.println("Loading Root CA Certificate...");
    sslClient.setCACert(root_ca);
    
    // 4. Setup MQTT
    setupMQTT();
}

// ==========================================
//              MAIN LOOP
// ==========================================
void loop() {
    if (!client.connected()) {
        reconnectMQTT();
    }
    client.loop();

    // --- READ SENSORS ---
    int co2Value = analogRead(PIN_ANALOG_CO2);
    int buttonValue = analogRead(PIN_ANALOG_BTN);
    
    if (buttonValue > 500) strcpy(currentRoom, "C101");
    else strcpy(currentRoom, "X003");

    snprintf(hmacSecretKey, sizeof(hmacSecretKey), hmacSecretKeyPrefix, currentRoom);

    int32_t rawTemp = readRawTemperature();
    float celsius = (float)compensateTemperature(rawTemp) / 100.0;

    if(celsius < -100.0) {
        Wire.begin();
        readCalibrationData();
    }

    int32_t rawHum = readRawHumidity();
    float humidity = compensateHumidity(rawHum);

    double distanceCm = readDistance();
    int isOccupied = (distanceCm > 0 && distanceCm < 300.0) ? 1 : 0;
    if (isOccupied == 0) {
        if (counterEmpty == 10) {
            loopTime = sleepTime;
        } else {
            counterEmpty++;
        }
    } else {
        loopTime = activeTime;
        counterEmpty = 0;
    }

    // --- SEND XBEE ---
    sendXbee('P', &co2Value, sizeof(int));
    if(celsius > -100.0) {
        sendXbee('T', &celsius, sizeof(float));
    }

    // --- PUBLISH MQTT ---
    char payload[150]; 
    unsigned long epochTime = WiFi.getTime(); // Will use the manually set time

    snprintf(payload, sizeof(payload), "{\"room\":\"%s\",\"value\":%.2f,\"timestamp\":%lu}", currentRoom, celsius, epochTime);
    publishToMQTT(topic_pub_temp, payload);

    snprintf(payload, sizeof(payload), "{\"room\":\"%s\",\"value\":%.2f,\"timestamp\":%lu}", currentRoom, humidity, epochTime);
    publishToMQTT(topic_pub_humi, payload);

    snprintf(payload, sizeof(payload), "{\"room\":\"%s\",\"value\":%d,\"timestamp\":%lu}", currentRoom, isOccupied, epochTime);
    publishToMQTT(topic_pub_pres, payload);

    snprintf(payload, sizeof(payload), "{\"room\":\"%s\",\"value\":%d,\"timestamp\":%lu}", currentRoom, co2Value, epochTime);
    publishToMQTT(topic_pub_co2, payload);

    // Debug Output
    Serial.print("Room: "); Serial.print(currentRoom);
    Serial.print(" | Temp: "); Serial.print(celsius);
    Serial.print(" | Hum: "); Serial.print(humidity);
    Serial.print(" | CO2: "); Serial.println(co2Value);

    delay(loopTime); 
}

// ==========================================
//          NETWORK FUNCTIONS
// ==========================================

void setupWiFi() {
    if (WiFi.status() == WL_NO_MODULE) {
        Serial.println("Communication with WiFi module failed!");
        while (true);
    }

    // Configure Static IP BEFORE begin
    WiFi.config(local_IP, gateway, subnet, dns);
    
    Serial.print("Connecting to SSID: ");
    Serial.println(ssid);

    while (WiFi.status() != WL_CONNECTED) {
        WiFi.begin(ssid, pass);
        Serial.print(".");
        delay(5000);
    }

    Serial.println("\nConnected to WiFi");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    // --- IMPORTANT: REMOVED NTP WAIT LOOP ---
    // Do NOT wait for WiFi.getTime() == 0 here. 
    // It will hang forever on offline networks.
}

void setupMQTT() {
    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(mqttCallback);
    // Increased timeout for slow handshakes
    client.setSocketTimeout(60);
}

// ... [Keep your reconnectMQTT, publishToMQTT, sensor, and XBee functions as they were] ...
// ... [Be sure to include all those functions at the bottom of the sketch] ...

void reconnectMQTT() {
    while (!client.connected()) {
        Serial.print("Connecting to MQTT...");
        
        // Connect with ID, User, Password
        if (client.connect(mqtt_client_id, "groupe3", "campus-iot")) {
            Serial.println("connected");
            
            // --- SUBSCRIBE HERE ONCE ---
            Serial.print("Subscribing to: ");
            Serial.println(topic_sub_heat);
            client.subscribe(topic_sub_heat, 1); // QoS 1
            
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5s");
            delay(5000);
        }
    }
}

void publishToMQTT(const char* topic, const char* payload) {
    // Attempt to publish with "Retained = false"
    // The library returns boolean true if the packet was successfully written to the network buffer
    boolean success = client.publish(topic, payload);
    
    // If it failed (Buffer full or connection lost), try to reconnect and resend ONCE
    if (!success) {
        Serial.print("Failed to publish to ");
        Serial.println(topic);
        
        // Force a quick reconnect check
        if (!client.connected()) {
            reconnectMQTT();
        }
        
        // Retry sending
        success = client.publish(topic, payload);
        
        if (success) {
            Serial.println("Retry successful!");
        } else {
            Serial.println("Retry failed. Message lost.");
        }
    } else {
       // Optional: Debug success
       // Serial.print("Sent to "); Serial.println(topic);
    }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("]: ");

    // 1. Convert Payload to String
    char message[length + 1];
    for (unsigned int i = 0; i < length; i++) {
        message[i] = (char)payload[i];
    }
    message[length] = '\0'; // Null-terminate
    Serial.println(message);

    // 2. Check if the topic matches our Heat Setpoint topic
    // We compare the incoming topic with our global constant
    if (strcmp(topic, topic_sub_heat) == 0) {
        
        // 3. Convert String to Float (Text "21.5" -> Float 21.5)
        float setpoint = atof(message);
        
        Serial.print("Bridging to XBee -> Type: H, Value: ");
        Serial.println(setpoint);

        // 4. Send via XBee
        // We use type 'H' (Heating) and pass the address of the float variable
        sendXbee('H', &setpoint, sizeof(float));
    }
}

// ==========================================
//           SENSOR FUNCTIONS
// ==========================================

double readDistance() {
    digitalWrite(PIN_ULTRASONIC_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_ULTRASONIC_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_ULTRASONIC_TRIG, LOW);

    long duration = pulseIn(PIN_ULTRASONIC_ECHO, HIGH);

    if (duration == 0) return -1.0; // Error value

    // Speed of sound: 0.0343 cm/us
    return (duration * 0.0343) / 2;
}

// --- XBEE Communication ---
void sendXbee(char type, void* value, int valSize) {
    // 1. Prepare the Data Buffer (Type + Value)
    // We need a temporary buffer to calculate the hash on
    byte dataBuffer[1 + valSize];
    dataBuffer[0] = (byte)type;
    memcpy(&dataBuffer[1], value, valSize);

    // 2. Calculate HMAC-SHA256
    SHA256 sha256;
    byte hmacResult[HMAC_SIZE];
    
    // Reset and initialize HMAC with the key
    sha256.resetHMAC(hmacSecretKey, strlen(hmacSecretKey));
    // Update with the data we want to sign
    sha256.update(dataBuffer, sizeof(dataBuffer));
    // Finalize and produce the 32-byte signature
    sha256.finalizeHMAC(hmacSecretKey, strlen(hmacSecretKey), hmacResult, HMAC_SIZE);

    // 3. Construct the ZigBee Packet
    // Total Payload = Data (Type + Value) + HMAC (32 bytes)
    int payloadDataSize = 1 + valSize + HMAC_SIZE;
    int packetLength = 14 + payloadDataSize; // 14 is the standard XBee header size

    byte packet[100]; // Ensure buffer is large enough (Header + Data + HMAC + Checksum)

    // -- Header (Standard ZigBee API Frame 0x10) --
    packet[0] = 0x10; // Frame Type: Transmit Request
    packet[1] = 0x01; // Frame ID
    
    // 64-bit Address (Broadcast)
    memset(&packet[2], 0x00, 8); 
    packet[8] = 0xFF; packet[9] = 0xFF; 
    
    // 16-bit Address
    packet[10] = 0xFF; packet[11] = 0xFE;
    
    // Radius & Options
    packet[12] = 0x00; packet[13] = 0x00;

    // -- Payload: Data --
    packet[14] = (byte)type;
    memcpy(&packet[15], value, valSize);

    // -- Payload: HMAC --
    // Append the calculated HMAC immediately after the data
    memcpy(&packet[15 + valSize], hmacResult, HMAC_SIZE);

    // -- Checksum Calculation --
    // The checksum covers everything AFTER the length bytes (which are handled by xbeeSerial.write)
    long sum = 0;
    for (int i = 0; i < packetLength; i++) {
        sum += packet[i];
    }
    byte checksum = 0xFF - (sum & 0xFF);

    // -- Physical Send --
    xbeeSerial.write(0x7E);             // Start Delimiter
    xbeeSerial.write((byte)(packetLength >> 8)); // Length MSB
    xbeeSerial.write((byte)(packetLength & 0xFF)); // Length LSB
    xbeeSerial.write(packet, packetLength);
    xbeeSerial.write(checksum);
}

// ==========================================
//          BME280 DRIVER (MANUAL)
// ==========================================

void readCalibrationData() {
    // Read Temperature Coefficients
    Wire.beginTransmission(BME280_ADDR);
    Wire.write(REG_CALIB_DIG_T1);
    Wire.endTransmission();
    Wire.requestFrom(BME280_ADDR, 6);
    if (Wire.available() < 6) return;
    dig_T1 = Wire.read() | (Wire.read() << 8);
    dig_T2 = Wire.read() | (Wire.read() << 8);
    dig_T3 = Wire.read() | (Wire.read() << 8);

    // Read Humidity Coefficients
    Wire.beginTransmission(BME280_ADDR);
    Wire.write(REG_CALIB_DIG_H1);
    Wire.endTransmission();
    Wire.requestFrom(BME280_ADDR, 1);
    dig_H1 = Wire.read();

    Wire.beginTransmission(BME280_ADDR);
    Wire.write(REG_CALIB_DIG_H2);
    Wire.endTransmission();
    Wire.requestFrom(BME280_ADDR, 7);
    if (Wire.available() < 7) return;
    
    uint8_t calib[7];
    for(int i=0; i<7; i++) calib[i] = Wire.read();

    dig_H2 = (int16_t)((calib[1] << 8) | calib[0]);
    dig_H3 = calib[2];
    dig_H4 = (int16_t)((calib[3] << 4) | (calib[4] & 0x0F));
    dig_H5 = (int16_t)((calib[5] << 4) | (calib[4] >> 4));
    dig_H6 = (int8_t)calib[6];
}

int32_t readRawTemperature() {
    // Set Forced Mode, Oversampling x1
    Wire.beginTransmission(BME280_ADDR);
    Wire.write(REG_CTRL_MEAS); 
    Wire.write(0x21); 
    Wire.endTransmission();
    delay(10); // Wait for measurement

    Wire.beginTransmission(BME280_ADDR);
    Wire.write(0xFA); // Temp MSB Register
    Wire.endTransmission();
    Wire.requestFrom(BME280_ADDR, 3);

    if (Wire.available() < 3) return 0;
    uint32_t msb = Wire.read();
    uint32_t lsb = Wire.read();
    uint32_t xlsb = Wire.read();
    return (msb << 12) | (lsb << 4) | (xlsb >> 4);
}

int32_t readRawHumidity() {
    // Ensure Hum oversampling is set
    Wire.beginTransmission(BME280_ADDR);
    Wire.write(REG_CTRL_HUM);
    Wire.write(0x01); 
    Wire.endTransmission();

    // Trigger measurement (Forced mode)
    Wire.beginTransmission(BME280_ADDR);
    Wire.write(REG_CTRL_MEAS);
    Wire.write(0x21); // Temp x1, Pres x1, Mode Forced
    Wire.endTransmission();
    delay(10); 

    Wire.beginTransmission(BME280_ADDR);
    Wire.write(REG_HUM_MSB);
    Wire.endTransmission();
    Wire.requestFrom(BME280_ADDR, 2);

    if (Wire.available() < 2) return 0;
    uint8_t msb = Wire.read();
    uint8_t lsb = Wire.read();
    return (msb << 8) | lsb;
}

// Returns Temperature in Celsius * 100 (e.g., 2550 = 25.50 C)
// Updates global t_fine
int32_t compensateTemperature(int32_t adc_T) {
    int32_t var1, var2;
    var1 = ((((adc_T >> 3) - ((int32_t)dig_T1 << 1))) * ((int32_t)dig_T2)) >> 11;
    var2 = (((((adc_T >> 4) - ((int32_t)dig_T1)) * ((adc_T >> 4) - ((int32_t)dig_T1))) >> 12) * ((int32_t)dig_T3)) >> 14;
    t_fine = var1 + var2;
    return (t_fine * 5 + 128) >> 8;
}

// Returns Humidity in %
float compensateHumidity(int32_t adc_H) {
    int32_t v_x1_u32r;
    v_x1_u32r = (t_fine - ((int32_t)76800));
    v_x1_u32r = (((((adc_H << 14) - (((int32_t)dig_H4) << 20) - (((int32_t)dig_H5) * v_x1_u32r)) + 
                ((int32_t)16384)) >> 15) * (((((((v_x1_u32r * ((int32_t)dig_H6)) >> 10) * (((v_x1_u32r * ((int32_t)dig_H3)) >> 11) + ((int32_t)32768))) >> 10) + 
                ((int32_t)2097152)) * ((int32_t)dig_H2) + 8192) >> 14));
    v_x1_u32r = (v_x1_u32r - (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * ((int32_t)dig_H1)) >> 4));
    v_x1_u32r = (v_x1_u32r < 0 ? 0 : v_x1_u32r);
    v_x1_u32r = (v_x1_u32r > 419430400 ? 419430400 : v_x1_u32r);
    return (float)(v_x1_u32r >> 12) / 1024.0;
}
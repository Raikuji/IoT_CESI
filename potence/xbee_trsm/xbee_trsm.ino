#include <SoftwareSerial.h>
#include <Wire.h>

#include <WiFiS3.h>
#include <PubSubClient.h>

SoftwareSerial xbeeSerial(2, 3); // RX, TX

#define BME280_ADDR 0x76  // Try 0x77 if 0x76 doesn't work
#define ID_REGISTER 0xD0
#define REG_HUM_MSB 0xFD
#define REG_CONTROL_HUM 0xF2
#define REG_CONTROL 0xF4

#define TRIG_PIN 4
#define ECHO_PIN 5

char ssid[] = "CESI_Iot";                                     // Nom du réseau
char pass[] =   "#RO_i0t.n3t";                                // Mot de passe du réseau (WPA)
int status = WL_IDLE_STATUS;                                  // Variable qui stocke l'état du réseau wifi

/** Variables en lien avec le MQTT**/
// --- Paramètres MQTT ---
const char* mqtt_server = "169.254.46.215"; // Adresse du serveur
const int mqtt_port = 1883;               // Port utilisé
const char* nameMQTT = "Groupe3_IoT";

// --- Création des TOPICS et des messages
const char* topic_pub_temp = "campus/orion/sensors/temperature";   // Nom du topic où l'on stocke l'information
const char* topic_pub_humi = "campus/orion/sensors/humidity";
const char* topic_pub_pres = "campus/orion/sensors/presence";

WiFiClient espClient;      
PubSubClient client(espClient);

// Calibration data variables
uint16_t dig_T1;
int16_t  dig_T2, dig_T3;
uint8_t  dig_H1;
int16_t  dig_H2;
uint8_t  dig_H3;
int16_t  dig_H4;
int16_t  dig_H5;
int8_t   dig_H6;
int32_t t_fine;

void setup() {
  Wire.begin();
  Serial.begin(9600);
  readCalibrationData();
  pinMode(TRIG_PIN, OUTPUT); // Sends the pulse
  pinMode(ECHO_PIN, INPUT);  // Receives the echo
  xbeeSerial.begin(9600);
  pinMode(D2, INPUT);
  wifiConnexion();
  printWifiData();
  connectionMQTT();
}

void loop() {

  int32_t adc_T = readRawTemperature();

  // 3. Convert Raw to Celsius using Bosch Formula
  int celsius = compensateTemperature(adc_T);

  Serial.print("Temperature: ");
  Serial.print((float)celsius/100.0);
  Serial.println(" °C");

  float tempFloat = (float)celsius/100.0;

  // 1. Lecture de la valeur analogique (0 à 1023)
  int sensorValue = analogRead(A0);
  
  sendXbee('P', &sensorValue, sizeof(int32_t));
  sendXbee('T', &tempFloat, sizeof(float));
  

  Serial.print("Valeur A0 envoyee : ");
  Serial.println(sensorValue);

  double dist = readDistance();
  char payloadPres[100] = "\0";
  strcat(payloadPres, "{\"room\":\"X003\",\"value\":");
  if(dist < 1000.0) {
    Serial.println("Occupation de la salle");
    strcat(payloadPres, "1");
  } else {
    strcat(payloadPres, "0");
  }
  strcat(payloadPres, "}");
  
  double temp = (double)celsius/100.0;
  char tempString[6];
  dtostrf(temp, 1, 2, tempString);
  char payloadTemp[100] = "\0";
  strcat(payloadTemp, "{\"room\":\"X003\",\"value\":");
  strcat(payloadTemp, tempString);
  strcat(payloadTemp, "}");

  double humidity = compensateHumidity(readRawHumidity());
  char humiString[6];
  dtostrf(humidity, 1, 2, humiString);
  char payloadHumi[100] = "\0";
  strcat(payloadHumi, "{\"room\":\"X003\",\"value\":");
  strcat(payloadHumi, humiString);
  strcat(payloadHumi, "}");
  Serial.print("Humidité : ");
  Serial.println(humidity);

  connectionMQTT();

  publish(topic_pub_temp, payloadTemp, nameMQTT);
  publish(topic_pub_humi, payloadHumi, nameMQTT);
  publish(topic_pub_pres, payloadPres, nameMQTT);
  
  delay(5000); // Envoi toutes les secondes
}

void sendXbee(char type, void* value, int valSize) {
  // 1. Calculate new payload size: 
  // Base frame (14 bytes) + Tag (1 byte) + Data (valSize bytes)
  int dataSize = 1 + valSize; 
  int pLen = 14 + dataSize; 
  
  byte payload[pLen];

  // 2. Standard Header (Type 0x10, ID, Addr64, Addr16, Radius, Opt)
  payload[0] = 0x10; payload[1] = 0x01;
  payload[2] = 0x00; payload[3] = 0x00; payload[4] = 0x00; payload[5] = 0x00;
  payload[6] = 0x00; payload[7] = 0x00; payload[8] = 0xFF; payload[9] = 0xFF;
  payload[10] = 0xFF; payload[11] = 0xFE;
  payload[12] = 0x00; payload[13] = 0x00;

  // 3. Add the TAG (The 'T' or 'P')
  payload[14] = (byte)type;

  // 4. Copy the raw bytes of the value (float or int) into the payload
  memcpy(&payload[15], value, valSize);

  // 5. Calculate Checksum
  long sum = 0;
  for (int i = 0; i < pLen; i++) sum += payload[i];
  byte checksum = 0xFF - (sum & 0xFF);

  // 6. Physical Send
  xbeeSerial.write(0x7E);
  xbeeSerial.write((byte)0x00);
  xbeeSerial.write((byte)pLen);
  xbeeSerial.write(payload, pLen);
  xbeeSerial.write(checksum);
}


void readCalibrationData() {
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(0x88); // Start of calibration registers
  Wire.endTransmission();
  Wire.requestFrom(BME280_ADDR, 6);

  dig_T1 = Wire.read() | (Wire.read() << 8);
  dig_T2 = Wire.read() | (Wire.read() << 8);
  dig_T3 = Wire.read() | (Wire.read() << 8);

  uint8_t calib[7];
  
  // Humidity calibration coefficients are in registers 0xE1 to 0xE7
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(0xE1);
  Wire.endTransmission();
  Wire.requestFrom(BME280_ADDR, 7);

  for (int i = 0; i < 7; i++) {
    calib[i] = Wire.read();
  }

  // Map the bytes to the variables
  dig_H2 = (int16_t)((calib[1] << 8) | calib[0]);
  dig_H3 = (uint8_t)calib[2];
  dig_H4 = (int16_t)((calib[3] << 4) | (calib[4] & 0x0F));
  dig_H5 = (int16_t)((calib[5] << 4) | (calib[4] >> 4));
  dig_H6 = (int8_t)calib[6];

  // H1 is special—it's located at register 0xA1
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(0xA1);
  Wire.endTransmission();
  Wire.requestFrom(BME280_ADDR, 1);
  dig_H1 = Wire.read();
}

double readDistance() {
  // 1. Clear the trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  // 2. Send a 10 microsecond pulse
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // 3. Read the travel time in microseconds
  long duration = pulseIn(ECHO_PIN, HIGH);

  // 4. Calculate distance: (Time * Speed of Sound) / 2
  // We divide by 2 because the sound travels to the object and back.
  float distanceCm = duration * 0.0343 / 2;

  // 5. Display the result
  if (duration == 0) {
    Serial.println("Out of range / No sensor found");
  } else {
    Serial.print("Distance: ");
    Serial.print(distanceCm);
    Serial.println(" cm");
  }
  return distanceCm;
}

int32_t readRawTemperature() {
  // Force a "forced mode" measurement (0xF4 control register)
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(0xF4); 
  Wire.write(0x21); // Pressure oversampling x1, Temp x1, Forced mode
  Wire.endTransmission();
  delay(10); // Wait for conversion

  Wire.beginTransmission(BME280_ADDR);
  Wire.write(0xFA); // Temperature MSB register
  Wire.endTransmission();
  Wire.requestFrom(BME280_ADDR, 3);

  uint32_t msb = Wire.read();
  uint32_t lsb = Wire.read();
  uint32_t xlsb = Wire.read();
  return (msb << 12) | (lsb << 4) | (xlsb >> 4);
}

int32_t readRawHumidity() {
  // 1. Humidity oversampling x1
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(REG_CONTROL_HUM);
  Wire.write(0x01); 
  Wire.endTransmission();

  // 2. Mode: Normal, Temp oversampling x1, Press oversampling x1
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(REG_CONTROL);
  Wire.write(0x27); 
  Wire.endTransmission();

  // Request 2 bytes from humidity registers
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(REG_HUM_MSB);
  Wire.endTransmission();
  
  Wire.requestFrom(BME280_ADDR, 2);
  
  if (Wire.available() == 2) {
    uint8_t msb = Wire.read();
    uint8_t lsb = Wire.read();
    int32_t raw_humidity = (msb << 8) | lsb;
    return raw_humidity;
  }
  return -1;
}

float compensateHumidity(int32_t adc_H) {
    int32_t v_x1_u32r;

    // t_fine is the fine temperature value calculated in the Temp function
    v_x1_u32r = (t_fine - ((int32_t)76800));

    v_x1_u32r = (((((adc_H << 14) - (((int32_t)dig_H4) << 20) - 
                (((int32_t)dig_H5) * v_x1_u32r)) + ((int32_t)16384)) >> 15) * (((((((v_x1_u32r * ((int32_t)dig_H6)) >> 10) * (((v_x1_u32r * ((int32_t)dig_H3)) >> 11) + ((int32_t)32768))) >> 10) + 
                ((int32_t)2097152)) * ((int32_t)dig_H2) + 8192) >> 14));

    v_x1_u32r = (v_x1_u32r - (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * ((int32_t)dig_H1)) >> 4));

    v_x1_u32r = (v_x1_u32r < 0 ? 0 : v_x1_u32r);
    v_x1_u32r = (v_x1_u32r > 419430400 ? 419430400 : v_x1_u32r);

    return (float)(v_x1_u32r >> 12) / 1024.0;
}

float compensateTemperature(int32_t adc_T) {
  int32_t var1, var2, T;
  var1 = ((((adc_T >> 3) - ((int32_t)dig_T1 << 1))) * ((int32_t)dig_T2)) >> 11;
  var2 = (((((adc_T >> 4) - ((int32_t)dig_T1)) * ((adc_T >> 4) - ((int32_t)dig_T1))) >> 12) * ((int32_t)dig_T3)) >> 14;
  t_fine = var1 + var2;
  T = (t_fine * 5 + 128) >> 8;
  return T;
}


void wifiConnexion(){                                           // Fonction qui initialise la connexion WIFI
  // Verrification du module WIFI
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Echec de la communication avec le module WIFI");
    // Arret du programme
     while (true);
  }

  // Mise en place de la connection WIFI
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("Connection en cours au SSID: ");
    Serial.println(ssid);
    configStaticIp();
    status = WiFi.begin(ssid, pass);
    delay(10000);
  }
  // Connection réussie
  Serial.print("Vous êtes connecté au WIFI"); 
}

void configStaticIp(){
  IPAddress local_IP(169, 254, 46, 14);
  IPAddress gateway(169, 254, 0, 1);
  IPAddress subnet(255, 255, 0, 0);

  WiFi.config(local_IP, gateway, subnet);
}

void printWifiData() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  Serial.print("Gateway IP Address: ");
  Serial.println(WiFi.gatewayIP());
  Serial.print("Subnet Mask: ");
  Serial.println(WiFi.subnetMask());
  Serial.print("DNS1 IP Address: ");
  Serial.println(WiFi.dnsIP(0));
}


void connectionMQTT(){
  client.setServer(mqtt_server, mqtt_port);

  while (!client.connected()) {
    Serial.print("Connexion au broker MQTT...");
    if (client.connect(nameMQTT)) {
      Serial.println("OK");
    } else {
      Serial.print("Erreur MQTT, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
  client.setCallback(callback);
}

void publish(const char* topic, const char* message, const char* nameMQTT){
  if (client.connected()) {
    // --- Envoi du message ---
    if (client.publish(topic, message)) {
      Serial.print("Message envoyé : ");
      Serial.println(message);
    } else {
      Serial.println("Erreur lors de l'envoi du message !");
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message reçu sur le topic: ");
  Serial.println(topic);

  Serial.print("Contenu: ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  Serial.println("-------------------");
}
#include <SoftwareSerial.h>
#include <Wire.h>

#include <WiFiS3.h>
#include <PubSubClient.h>

SoftwareSerial xbeeSerial(2, 3); // RX, TX

#define BME280_ADDR 0x76  // Try 0x77 if 0x76 doesn't work
#define ID_REGISTER 0xD0

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
const char* topic_pub = "campus/orion/sensors/temperature";   // Nom du topic où l'on stocke l'information

WiFiClient espClient;      
PubSubClient client(espClient);

// Calibration data variables
uint16_t dig_T1;
int16_t  dig_T2, dig_T3;
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

  // 1. Lecture de la valeur analogique (0 à 1023)
  int sensorValue = analogRead(A0);
  
  // 2. Préparation des données (Payload)
  byte valHigh = highByte(celsius);
  byte valLow = lowByte(celsius);

  // 3. Construction de la trame 0x10
  // Structure : Type(1), ID(1), Addr64(8), Addr16(2), Radius(1), Opt(1), Data(2) = 16 octets
  byte payload[] = {
    0x10, 0x01, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, // Destination Broadcast
    0xFF, 0xFE, 
    0x00, 0x00, 
    valHigh, valLow                                 // Nos 2 octets de A0
  };

  // 4. Calcul du Checksum
  int pLen = sizeof(payload);
  long sum = 0;
  for (int i = 0; i < pLen; i++) sum += payload[i];
  byte checksum = 0xFF - (sum & 0xFF);

  // 5. Envoi physique
  xbeeSerial.write(0x7E);           // Start
  xbeeSerial.write((byte)0x00);     // Length MSB
  xbeeSerial.write((byte)pLen);     // Length LSB
  xbeeSerial.write(payload, pLen);  // Content
  xbeeSerial.write(checksum);       // Checksum

  Serial.print("Valeur A0 envoyee : ");
  Serial.println(sensorValue);

  

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

  double temp = (double)celsius/100.0;
  char tempString[6];
  dtostrf(temp, 1, 2, tempString);
  char payloadTemp[100] = "\0";
  strcat(payloadTemp, "{\"room\":\"X003\",\"value\":");
  strcat(payloadTemp, tempString);
  strcat(payloadTemp, "}");
  Serial.println(payloadTemp);

  publish(topic_pub, payloadTemp, nameMQTT);
  
  delay(5000); // Envoi toutes les secondes
}


void readCalibrationData() {
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(0x88); // Start of calibration registers
  Wire.endTransmission();
  Wire.requestFrom(BME280_ADDR, 6);

  dig_T1 = Wire.read() | (Wire.read() << 8);
  dig_T2 = Wire.read() | (Wire.read() << 8);
  dig_T3 = Wire.read() | (Wire.read() << 8);
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
  client.subscribe(topic_pub);   // abonnement ici
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
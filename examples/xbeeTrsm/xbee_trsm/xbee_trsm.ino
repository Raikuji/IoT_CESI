#include <SoftwareSerial.h>

SoftwareSerial xbeeSerial(2, 3); // RX, TX

void setup() {
  Serial.begin(9600);
  xbeeSerial.begin(9600);
  pinMode(D2, INPUT);
  Serial.println("Emetteur pret - Lecture A0 en cours...");
}

void loop() {
  // 1. Lecture de la valeur analogique (0 à 1023)
  int sensorValue = analogRead(A0);
  
  // 2. Préparation des données (Payload)
  byte valHigh = highByte(sensorValue);
  byte valLow = lowByte(sensorValue);

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
  
  delay(1000); // Envoi toutes les secondes
}
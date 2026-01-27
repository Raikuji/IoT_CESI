#include <SoftwareSerial.h>

SoftwareSerial xbeeSerial(2, 3); // RX, TX

void setup() {
  Serial.begin(9600);
  xbeeSerial.begin(9600);
  Serial.println("Emetteur XBee - Mode API (Trame 0x10)");
}

void loop() {
  int sensorValue = analogRead(A0); // La donnée à envoyer
  
  sendApiFrame(sensorValue);
  
  delay(2000); 
}

void sendApiFrame(int value) {
  // Décomposition de la valeur (int 16 bits) en 2 octets
  byte dataHigh = highByte(value);
  byte dataLow = lowByte(value);

  // Construction de la trame 0x10 (sans le header et la longueur)
  // Frame Type (0x10), Frame ID (0x01), Destination 64 bits (0x00...FFFF pour Broadcast), 
  // Destination 16 bits (0xFFFE), Broadcast Radius (0x00), Options (0x00), Data...
  byte payload[] = {
    0x10, 0x01, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, // Adresse 64-bit (Broadcast)
    0xFF, 0xFE,                                     // Adresse 16-bit
    0x00,                                           // Broadcast radius
    0x00,                                           // Options
    dataHigh, dataLow                               // NOS DONNÉES
  };

  int payloadSize = sizeof(payload);
  
  // Calcul du Checksum
  long sum = 0;
  for (int i = 0; i < payloadSize; i++) {
    sum += payload[i];
  }
  byte checksum = 0xFF - (sum & 0xFF);

  // ENVOI DE LA TRAME COMPLETE
  xbeeSerial.write(0x7E);           // Delimiter
  xbeeSerial.write((byte)0x00);     // Length High
  xbeeSerial.write((byte)payloadSize); // Length Low
  xbeeSerial.write(payload, payloadSize);
  xbeeSerial.write(checksum);

  Serial.print("Trame API envoyee. Valeur: ");
  Serial.println(value);
}
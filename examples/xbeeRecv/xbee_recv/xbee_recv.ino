#include <SoftwareSerial.h>

SoftwareSerial xbeeSerial(2, 3); // RX, TX

void setup() {
  Serial.begin(9600);
  xbeeSerial.begin(9600);
  Serial.println("Recepteur XBee - Mode API pret...");
}

void loop() {
  // 1. Chercher le début de la trame (0x7E)
  if (xbeeSerial.available() > 0) {
    if (xbeeSerial.read() == 0x7E) {
      handleApiFrame();
    }
  }
}

void handleApiFrame() {
  // Attendre que la longueur (2 octets) soit disponible
  while (xbeeSerial.available() < 2);
  int length = (xbeeSerial.read() << 8) | xbeeSerial.read();

  // Attendre que tout le contenu (payload + checksum) soit arrivé
  while (xbeeSerial.available() < length + 1);

  byte frameType = xbeeSerial.read();
  
  // On ne traite que les trames de réception Zigbee (0x90)
  if (frameType == 0x90) {
    // Sauter les adresses (8 octets 64-bit + 2 octets 16-bit + 1 octet options)
    for (int i = 0; i < 11; i++) {
      xbeeSerial.read();
    }

    // Lire les données utiles (Data)
    // Dans notre émetteur, on envoyait 2 octets (int)
    byte dataHigh = xbeeSerial.read();
    byte dataLow = xbeeSerial.read();
    
    // Reconstitution de la valeur
    int receivedValue = (dataHigh << 8) | dataLow;

    // Lire le checksum (dernier octet) pour vider le buffer
    byte checksum = xbeeSerial.read();

    // Affichage des résultats
    Serial.print("Nouvelle donnee recue : ");
    Serial.println(receivedValue);
  } 
  else {
    // Si c'est un autre type de trame, on vide le reste pour ne pas bloquer
    for (int i = 0; i < length; i++) xbeeSerial.read();
  }
}
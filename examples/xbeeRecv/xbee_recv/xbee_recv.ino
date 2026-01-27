#include <LiquidCrystal.h>

// XBee on UNO R4 WiFi uses Serial1 (D0/D1)
// LCD pins: RS=12, E=11, D4=5, D5=4, D6=3, D7=2
const int LCD_RS = 12;
const int LCD_E  = 11;
const int LCD_D4 = 5;
const int LCD_D5 = 4;
const int LCD_D6 = 3;
const int LCD_D7 = 2;

LiquidCrystal lcd(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7);
const float TEMP_SCALE = 100.0f; // 2350 -> 23.50 C (change to 10.0 if needed)

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("XBee API RX");
  lcd.setCursor(0, 1);
  lcd.print("Waiting...");
  Serial.println("Recepteur XBee - Mode API pret...");
}

void loop() {
  // 1. Chercher le début de la trame (0x7E)
  if (Serial1.available() > 0) {
    if (Serial1.read() == 0x7E) {
      handleApiFrame();
    }
  }
}

void handleApiFrame() {
  // Attendre que la longueur (2 octets) soit disponible
  while (Serial1.available() < 2);
  int length = (Serial1.read() << 8) | Serial1.read();

  // Attendre que tout le contenu (payload + checksum) soit arrivé
  while (Serial1.available() < length + 1);

  byte frameType = Serial1.read();
  
  // On ne traite que les trames de réception Zigbee (0x90)
  if (frameType == 0x90) {
    // Sauter les adresses (8 octets 64-bit + 2 octets 16-bit + 1 octet options)
    for (int i = 0; i < 11; i++) {
      Serial1.read();
    }

    // Lire les données utiles (Data)
    // Dans notre émetteur, on envoyait 2 octets (int)
    byte dataHigh = Serial1.read();
    byte dataLow = Serial1.read();
    
    // Reconstitution de la valeur
    int receivedValue = (dataHigh << 8) | dataLow;
    float tempC = receivedValue / TEMP_SCALE;

    // Lire le checksum (dernier octet) pour vider le buffer
    byte checksum = Serial1.read();

    // Affichage des résultats
    Serial.print("Nouvelle donnee recue : ");
    Serial.println(receivedValue);

    lcd.setCursor(0, 1);
    lcd.print("                ");
    lcd.setCursor(0, 1);
    lcd.print("TEMP: ");
    lcd.print(tempC, 1);
    lcd.print(" C");
  } 
  else {
    // Si c'est un autre type de trame, on vide le reste pour ne pas bloquer
    for (int i = 0; i < length; i++) Serial1.read();
  }
}
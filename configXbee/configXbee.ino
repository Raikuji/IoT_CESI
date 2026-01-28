#include <SoftwareSerial.h>

SoftwareSerial xbee(2, 3); // RX, TX

void setup() {
  Serial.begin(9600);   // USB
  xbee.begin(9600);    // XBee
}

void loop() {
  if (xbee.available()){
    Serial.write(xbee.read());
 }
  if (Serial.available()){
    xbee.write(Serial.read());
}
}

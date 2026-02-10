# Documentation IoT - Campus CESI Nancy
## Guide utilisateur (Hardware & Firmware)

> Guide pour configurer, déployer et utiliser les capteurs et actionneurs du bâtiment Orion.

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Matériel requis](#-matériel-requis)
- [Installation des capteurs](#-installation-des-capteurs)
- [Configuration Gateway Arduino](#-configuration-gateway-arduino)
- [Configuration XBee (ZigBee)](#-configuration-xbee-zigbee)
- [Bridge MQTT (Python)](#-bridge-mqtt-python)
- [Tests et validation](#-tests-et-validation)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Vue d'ensemble

Architecture IoT du bâtiment Orion :

```
Capteurs (XBee) → Gateway Arduino → Bridge Python → MQTT Broker → Backend API
```

### Schéma détaillé (PlantUML)

Voir [architecture_iot.puml](architecture_iot.puml) pour le schéma complet visualisable en temps réel.

```plantuml
@startuml Campus_IoT_Architecture
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

title Campus IoT - CESI Nancy\nArchitecture complète de la chaîne IoT

' Définir les couleurs
!define LEGEND_BG #E8F4F8
!define SENSOR_COLOR #FFB6C1
!define NETWORK_COLOR #87CEEB
!define SERVER_COLOR #90EE90
!define DB_COLOR #DDA0DD
!define CLIENT_COLOR #F0E68C

package "CAPTEURS IOT\n(Bâtiment Orion)" <<frame>> {
    card Sensor1 [
        **BME280**
        ----
        Température
        Humidité
        Pression
    ] #SENSOR_COLOR
    
    card Sensor2 [
        **HC-SR04**
        ----
        Distance
        Présence
    ] #SENSOR_COLOR
    
    card Sensor3 [
        **Potentiomètre**
        ----
        Luminosité (ADC)
    ] #SENSOR_COLOR
    
    card Sensor4 [
        **MQ-135**
        ----
        CO2
    ] #SENSOR_COLOR
}

package "GATEWAY LOCAL\n(Collecteur)" <<frame>> {
    card Arduino [
        **Arduino Mega 2560**
        ----
        I2C: BME280
        GPIO: HC-SR04
        ADC: Potentiomètre
        Serial OUT: 9600 baud
    ] #SERVER_COLOR
    
    card XBeeCoord [
        **XBee Coordinator**
        ----
        ZigBee Mesh
        PAN ID: 1234
        Channel: 15
    ] #NETWORK_COLOR
    
    card Actuator1 [
        **Moteur DC**
        ----
        PWM Pin 5
        Relay driver
    ] #SERVER_COLOR
    
    card Actuator2 [
        **Speaker**
        ----
        PWM Pin 6
        Audio driver
    ] #SERVER_COLOR
}

package "CAPTEURS DISTANTS\n(XBee End Devices)" <<frame>> {
    card XBeeEND1 [
        **XBee End Device #1**
        ----
        Capteur BME280
        Routeur local
    ] #NETWORK_COLOR
    
    card XBeeEND2 [
        **XBee End Device #2**
        ----
        Capteur HC-SR04
        Routeur local
    ] #NETWORK_COLOR
}

package "GATEWAY APPLICATION\n(PC/Serveur)" <<frame>> {
    card Bridge [
        **mqtt_bridge.py**
        ----
        Lit port série Arduino
        Parse JSON
        Publie MQTT
        Reçoit commandes
    ] #SERVER_COLOR
}

package "BROKER MQTT\n(Mosquitto)" <<frame>> {
    card MQTTBroker [
        **Mosquitto Broker**
        ----
        Port 1883: MQTT TCP
        Port 9001: WebSocket
        Topics: campus/orion/*
        QoS: 0/1/2
    ] #NETWORK_COLOR
}

package "BACKEND\n(FastAPI)" <<frame>> {
    card API [
        **FastAPI Server**
        ----
        REST Endpoints
        WebSocket Server
        MQTT Client
        JWT Auth
    ] #SERVER_COLOR
    
    card Services [
        **Services**
        ----
        Sensor Manager
        Alert Manager
        Energy Manager
        Security Service
    ] #SERVER_COLOR
}

package "DATABASE\n(Supabase Cloud)" <<frame>> {
    card DB [
        **PostgreSQL**
        + **TimescaleDB**
        ----
        Sensors data
        Alerts history
        Users & logs
        Energy profiles
    ] #DB_COLOR
}

package "FRONTEND\n(Client Web)" <<frame>> {
    card WebUI [
        **Vue 3 + Vuetify**
        ----
        Dashboard
        Alerts view
        Admin panel
        Real-time charts
    ] #CLIENT_COLOR
}

' Relations Capteurs -> Gateway
Sensor1 -.I2C.-> Arduino : "I2C\n(SDA/SCL)"
Sensor2 -.GPIO.-> Arduino : "GPIO\n(TRIG/ECHO)"
Sensor3 -.ADC.-> Arduino : "Analog\n(A0)"
Sensor4 -.I2C.-> Arduino : "I2C"

' Relations Actionneurs <- Gateway
Arduino -.PWM.-> Actuator1 : "PWM Pin 5"
Arduino -.PWM.-> Actuator2 : "PWM Pin 6"

' Relations XBee
Arduino ---"ZigBee\nMesh"---> XBeeCoord
XBeeCoord ---"ZigBee (30m)"---> XBeeEND1
XBeeCoord ---"ZigBee (30m)"---> XBeeEND2

' Relations Serial
Arduino ===o"Serial 9600 baud"o=== Bridge : "USB"

' Relations MQTT
Bridge ---"MQTT TCP\nPort 1883"---> MQTTBroker
API ---"MQTT Client"---> MQTTBroker
MQTTBroker ---"Topics:\nsensors/*\nactuators/*"---> API

' Relations API <-> DB
API ===o"TCP 5432"o=== DB

' Relations Frontend <-> Backend
WebUI ---"HTTP REST\n/api/*"---> API
WebUI ---"WebSocket\n/ws"---> API
API ---"JSON Push\n(real-time)"---> WebUI

' Légende flux de données
legend right
    |<#FFE4E1> Capteurs locaux (Serial/I2C/GPIO) |
    |<#87CEEB> Communication (ZigBee, MQTT, TCP) |
    |<#90EE90> Traitement (Gateway, Services) |
    |<#DDA0DD> Persistance (Database) |
    |<#F0E68C> Présentation (Frontend) |
endlegend

note bottom of Sensor1
  **Format capteur local:**
  Mesure continue
  Envoi à Arduino
  Sérialisé en JSON
end note

note bottom of XBeeCoord
  **ZigBee Mesh:**
  - Portée ~30m indoor
  - Auto-healing
  - Jusqu'à 65k nœuds
  - Débit 250 kbps
end note

note bottom of MQTTBroker
  **Topics:**
  campus/orion/sensors/temperature
  campus/orion/sensors/humidity
  campus/orion/actuators/motor
  campus/orion/controls/energy/{id}
end note

note bottom of API
  **Latence estimée:**
  XBee: 50ms
  MQTT: 100ms
  WebSocket: 50ms
  UI Render: 800ms
  **Total: <2s**
end note

@enduml
```

**Rôles :**
- **Capteurs** : Mesurent température, humidité, CO2, présence, distance
- **Gateway Arduino** : Reçoit les données XBee, les transmet en série vers le PC
- **Bridge Python** : Convertit données série en messages MQTT publiés
- **Broker MQTT** : Centralise les messages reçus, les backend/frontend s'y abonnent

---

## 🛠️ Matériel requis

| Composant | Quantité | Rôle |
|-----------|----------|------|
| Arduino Mega 2560 | 1 | Gateway centrale |
| XBee Series 2 (Coordinator) | 1 | Coordinateur réseau ZigBee |
| XBee Series 2 (Router/End Device) | N | Capteurs/Actionneurs |
| BME280 (I2C) | N | Température, Humidité, Pression |
| HC-SR04 (Ultrasonic) | N | Distance/Présence |
| Potentiomètre | N | Simulation luminosité |
| MQ-135 | N | CO2 (optionnel) |
| Moteur DC + Driver | 1 | Actionneur ventilation |
| Speaker + Driver audio | 1 | Actionneur alarmes |
| Câbles USB, Breadboards, Résistances pull-up (4.7kΩ) | - | Connexions |
| PC/Serveur (Linux/macOS) | 1 | Exécute Bridge Python + Backend |

---

## 📦 Installation des capteurs

### 1. BME280 (Température/Humidité/Pression)

**Câblage (I2C) :**
```
BME280 → Arduino Mega
VCC → 3.3V
GND → GND
SCL → Pin 21
SDA → Pin 20
```

**Code exemple (Arduino) :**
```cpp
#include <Wire.h>
#include <Adafruit_BME280.h>

Adafruit_BME280 bme;

void setup() {
  Serial.begin(9600);
  if (!bme.begin(0x77)) {
    Serial.println("BME280 not found!");
    while (1);
  }
}

void loop() {
  float temp = bme.readTemperature();
  float humidity = bme.readHumidity();
  float pressure = bme.readPressure();
  
  Serial.print(temp);
  Serial.print(",");
  Serial.println(humidity);
  delay(1000);
}
```

### 2. HC-SR04 (Distance/Présence)

**Câblage :**
```
HC-SR04 → Arduino Mega
VCC → 5V
GND → GND
TRIG → Pin 7
ECHO → Pin 8
```

**Code exemple :**
```cpp
const int trigPin = 7;
const int echoPin = 8;

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2;
  
  Serial.println(distance);
  delay(1000);
}
```

### 3. Potentiomètre (Luminosité)

**Câblage :**
```
Potentiomètre → Arduino Mega
VCC → 5V
GND → GND
OUT → Pin A0
```

**Code exemple :**
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  int lightLevel = analogRead(A0);
  float percent = (lightLevel / 1023.0) * 100;
  
  Serial.println(percent);
  delay(1000);
}
```

### 4. Moteur DC + Relay

**Câblage :**
```
Relay IN → Pin 5 (PWM)
Relay GND → GND
Moteur → Relay NO/COM
```

**Code exemple :**
```cpp
const int motorPin = 5;

void setup() {
  Serial.begin(9600);
  pinMode(motorPin, OUTPUT);
}

void loop() {
  int speed = 150; // 0-255
  analogWrite(motorPin, speed);
  delay(1000);
}
```

---

## ⚙️ Configuration Gateway Arduino

### Étape 1 : Assembler le circuit

- Arduino Mega connecté au PC via USB
- XBee Coordinator inséré sur le shield XBee
- Capteurs câblés sur les pins appropriés (voir sections ci-dessus)

### Étape 2 : Flasher le code

```bash
# 1. Ouvrir Arduino IDE
# 2. Fichier → Exemples → Utiliser gateway.ino du projet
# 3. Sélectionner la carte "Arduino Mega 2560"
# 4. Sélectionner le port COM (ex: /dev/ttyUSB0 ou COM3)
# 5. Téléverser
```

**Codes de la Gateway :** [firmware/gateway/gateway.ino](firmware/gateway/gateway.ino)

### Étape 3 : Vérifier la communication

```bash
# Via Arduino IDE → Moniteur série
# Vous devriez voir les lectures des capteurs
# Ex: TEMP:23.5,HUM:45,PRESS:1013
```

---

## 📡 Configuration XBee (ZigBee)

### 1. Préparation

- **Coordinator** : doit être sur la Gateway Arduino
- **End Devices / Routers** : sur chaque capteur distant

### 2. Configuration du Coordinator (Gateway)

```bash
# Via XCTU (XBee Configuration and Test Utility)
# 1. Connecter Arduino au PC
# 2. Lancer XCTU
# 3. Ajouter le port de l'Arduino
# 4. Charger le firmware Coordinator (disponible dans XCTU)
# 5. Configurer le PAN ID (ex: 1234)
# 6. Configurer le Channel (ex: 15)
# 7. Écrire les paramètres
```

### 3. Configuration des End Devices (Capteurs)

```bash
# Pour chaque capteur XBee :
# 1. Brancher le capteur XBee via adaptateur USB (ou via Arduino)
# 2. Lancer XCTU
# 3. Charger le firmware End Device
# 4. Configurer avec le même PAN ID et Channel que le Coordinator
# 5. Écrire les paramètres

# Paramètres clés :
# - PAN ID: 1234 (doit être identique au Coordinator)
# - Channel: 15 (doit être identique)
# - DL (Destination Low): 0 (broadcast vers Coordinator)
# - DH (Destination High): 0
```

### 4. Vérifier la formation du réseau

```bash
# Dans XCTU, via l'onglet Consola ou Network Viewer :
# - Le Coordinator doit voir les End Devices rejoindre
# - Status LED sur le XBee doit être verte/clignotante
```

---

## 🐍 Bridge MQTT (Python)

### Installation

```bash
cd campus-iot/firmware/gateway
pip install -r ../requirements.txt
```

### Configuration

Fichier `mqtt_bridge.py` doit configurer :

```python
# Paramètres série
SERIAL_PORT = "/dev/ttyACM0"  # À adapter : COM3 (Windows), /dev/ttyUSB0 (Linux)
BAUD_RATE = 9600

# Paramètres MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "campus/orion"

# Capteurs mappés
SENSORS = {
    "temperature": "sensors/temperature",
    "humidity": "sensors/humidity",
    "pressure": "sensors/pressure",
    "distance": "sensors/distance",
    "light": "sensors/light"
}
```

### Lancement

```bash
# En développement
python mqtt_bridge.py

# Ou en arrière-plan
nohup python mqtt_bridge.py > mqtt_bridge.log 2>&1 &
```

### Commandes interactives

Une fois lancé, vous pouvez taper dans le terminal :

```
> temp              # Lire température
> hum               # Lire humidité
> dist              # Lire distance
> motor 150         # Contrôler moteur (0-255)
> pub X101 temp 23  # Publier une donnée
> pub X101 hum 45
> help              # Afficher l'aide
```

---

## ✅ Tests et validation

### Test 1 : Vérifier la liaision série

```bash
# Linux/macOS
screen /dev/ttyACM0 9600
# Vous devriez voir les données du capteur
# Quitter : Ctrl+A, K, Y

# Ou avec pyserial
python -c "
import serial
ser = serial.Serial('/dev/ttyACM0', 9600)
while True:
    print(ser.readline().decode())
"
```

### Test 2 : Vérifier MQTT

```bash
# Terminal 1 : S'abonner aux capteurs
mosquitto_sub -h localhost -p 1883 -t "campus/orion/sensors/#"

# Terminal 2 : Lancer le bridge
python mqtt_bridge.py

# Vous devriez voir les messages apparaître dans le Terminal 1
# Ex: campus/orion/sensors/temperature {"room": "X101", "value": 23.5}
```

### Test 3 : Vérifier WebSocket

```bash
# Dans le navigateur, ouvrir http://localhost
# Aller dans le Dashboard
# Vérifier que les données temps réel arrivent
# Ouvrir la console (F12) pour voir les logs WebSocket
```

### Test 4 : Tester les actionneurs

```bash
# Publier une commande
mosquitto_pub -h localhost -p 1883 \
  -t "campus/orion/actuators/motor" \
  -m '{"room": "X101", "value": 200}'

# Le moteur devrait se mettre en mouvement
```

---

## 🐛 Troubleshooting

### Pas de données sur le port série

**Causes possibles :**
- Arduino n'est pas flashé correctement → Re-flasher
- Port série incorrect → Vérifier le port dans Arduino IDE
- Capteur non connecté → Vérifier le câblage
- Baud rate incorrect → Vérifier 9600 en code et en bridge

**Actions :**
```bash
# Lister les ports disponibles
ls -la /dev/tty*

# Vérifier qu'Arduino est reconnu
lsusb | grep Arduino
```

### XBee ne reçoit pas les capteurs

**Causes possibles :**
- Réseau XBee pas formé → Vérifier PAN ID et Channel
- Portée insuffisante → Placer plus près du Coordinator
- Capteur hors batterie → Vérifier l'alimentation

**Actions :**
```bash
# Dans XCTU : Network Viewer
# Vérifier que les appareils sont connectés et montrent une force de signal
```

### MQTT ne reçoit pas les données

**Causes possibles :**
- Bridge MQTT pas lancé → Lancer `python mqtt_bridge.py`
- Broker MQTT pas accessible → Vérifier Mosquitto `docker ps`
- Topic incorrect → Vérifier le préfixe `campus/orion`

**Actions :**
```bash
# Vérifier que le broker écoute
mosquitto_sub -h localhost -p 1883 -t "\$SYS/#"

# Vérifier la connexion du bridge
tail -f mqtt_bridge.log
```

### Moteur/Speaker ne réagit pas aux commandes

**Causes possibles :**
- Actionneur pas alimenté → Vérifier l'alimentation du relay/driver
- Pin PWM incorrecte → Vérifier le code Arduino
- Commandé sur le mauvais topic → Vérifier le topic exact

**Actions :**
```bash
# Publier avec verbose
mosquitto_pub -h localhost -p 1883 -v \
  -t "campus/orion/actuators/motor" \
  -m '{"room": "X101", "value": 150}'

# Vérifier dans le moniteur série Arduino
# Vous devriez voir la commande reçue
```

### Latence capteur → Dashboard > 2s

**Causes possibles :**
- Fréquence d'acquisition trop basse → Augmenter dans le profil énergétique
- Réseau XBee surchargé → Réduire le nombre de capteurs ou augmenter l'intervalle
- WebSocket pas optimisé → Vérifier les paramètres de reconnexion

**Actions :**
```bash
# Mesurer la latence manuellement
# 1. Noter l'heure sur Arduino
# 2. Lire dans le Dashboard
# 3. Calculer la différence

# Si > 2s, ajuster le profil énergie dans l'admin web
```

---

## 📊 Checklist de déploiement

- [ ] Arduino Mega flashé avec gateway.ino
- [ ] XBee Coordinator configuré et sur le port série
- [ ] XBee End Devices configurés avec le même PAN ID/Channel
- [ ] Capteurs câblés et testés (moniteur série)
- [ ] Bridge MQTT lancé et reçoit les données
- [ ] Mosquitto tourne (Docker)
- [ ] Backend reçoit les MQTT et les publie via WebSocket
- [ ] Frontend affiche les données en temps réel
- [ ] Actionneurs réagissent aux commandes
- [ ] Alertes se créent automatiquement sur seuils dépassés

---

## 📞 Support

- **Problème de capteur** : Vérifier le code Arduino, le câblage, les pins
- **Problème de XBee** : Vérifier XCTU, PAN ID, Channel, portée
- **Problème MQTT** : Vérifier le bridge Python, les topics, Mosquitto
- **Problème web** : Voir [README.md - Dépannage](README.md#-dépannage-debug)

---

**Dernière mise à jour** : 10 février 2026

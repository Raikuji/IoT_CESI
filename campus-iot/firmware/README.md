# Campus IoT - Firmware

Code Arduino et Python pour connecter les capteurs et actionneurs à l'application web.

## Architecture

```
┌─────────────┐    ZigBee    ┌─────────────┐    USB     ┌─────────────┐    MQTT    ┌─────────────┐
│  Capteurs/  │ ──────────►  │   Gateway   │ ────────►  │   Bridge    │ ────────►  │  Mosquitto  │
│ Actionneurs │    (XBee)    │  (Arduino)  │  Serial    │  (Python)   │            │  (Docker)   │
└─────────────┘              └─────────────┘            └─────────────┘            └─────────────┘
```

## Contenu

```
firmware/
├── gateway/
│   ├── gateway.ino              # Arduino: reçoit XBee, envoie au bridge
│   └── mqtt_bridge.py           # Python: lit Serial, publie MQTT
│
├── transmitter_bme280/
│   └── transmitter_bme280.ino   # Capteur température/humidité (BME280)
│
├── transmitter_ultrasonic/
│   └── transmitter_ultrasonic.ino  # Capteur présence (HC-SR04)
│
├── transmitter_potentiometer/
│   └── transmitter_potentiometer.ino  # Capteur niveau/lumière (potentiomètre)
│
├── actuator_motor/
│   └── actuator_motor.ino       # Actionneur moteur/servo (HTEC HS-905BB+)
│
├── actuator_speaker/
│   └── actuator_speaker.ino     # Actionneur buzzer/alertes sonores
│
├── requirements.txt             # Dépendances Python
└── README.md                    # Ce fichier
```

## Capteurs supportés

| Composant | Type | Fichier | Topics MQTT |
|-----------|------|---------|-------------|
| **BME280** | Température + Humidité | `transmitter_bme280/` | `sensors/temperature`, `sensors/humidity` |
| **HC-SR04** | Présence (ultrason) | `transmitter_ultrasonic/` | `sensors/presence` |
| **Potentiomètre** | Niveau/Lumière | `transmitter_potentiometer/` | `sensors/light` |

## Actionneurs supportés

| Composant | Type | Fichier | Commandes |
|-----------|------|---------|-----------|
| **Servo (HTEC HS-905BB+)** | Moteur | `actuator_motor/` | `0-100`, `open`, `close`, `toggle` |
| **Buzzer/Speaker** | Alertes sonores | `actuator_speaker/` | `beep`, `warning`, `danger`, `co2`, `stop` |

## Installation

### 1. Préparer l'environnement Python

```bash
cd firmware
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Trouver le port série Arduino

```bash
# macOS
ls /dev/cu.usb*

# Linux
ls /dev/ttyUSB* /dev/ttyACM*

# Windows: voir Gestionnaire de périphériques
```

### 3. Configurer le bridge

Éditer `gateway/mqtt_bridge.py` :

```python
SERIAL_PORT = "/dev/cu.usbmodem14101"  # <-- Votre port
DEFAULT_ROOM = "X101"  # <-- Salle par défaut
```

### 4. Uploader le code Arduino

Avec Arduino IDE :
1. Ouvrir le fichier `.ino` souhaité
2. Sélectionner la carte : Arduino UNO R4 WiFi
3. Sélectionner le port
4. Upload

## Utilisation

### Lancer le bridge

```bash
# Assurez-vous que Docker tourne
cd ../
docker-compose up -d

# Lancer le bridge
cd firmware
source venv/bin/activate
python gateway/mqtt_bridge.py
```

### Commandes de test (dans le bridge)

**Capteurs :**
```
> temp 23.5          # Température 23.5°C
> hum 45             # Humidité 45%
> pres 1             # Présence détectée
> light 75           # Niveau lumière 75%
```

**Actionneurs :**
```
> motor 50           # Moteur à 50%
> motor open         # Moteur ouvert (100%)
> motor close        # Moteur fermé (0%)
> speaker beep       # Bip simple
> speaker warning    # Son d'avertissement
> speaker danger     # Alarme
> speaker co2        # Alerte CO2
> speaker stop       # Silence
```

**Avancé :**
```
> pub X108 temp 22   # Publier pour une salle spécifique
> cmd X108 motor 75  # Commande pour une salle spécifique
```

## Topics MQTT

### Capteurs (sensors)

Format : `campus/orion/{ROOM}/sensors/{TYPE}`

| Topic | Description | Valeurs |
|-------|-------------|---------|
| `.../sensors/temperature` | Température | Float (°C) |
| `.../sensors/humidity` | Humidité | Float (%) |
| `.../sensors/presence` | Présence | 0 ou 1 |
| `.../sensors/light` | Luminosité | 0-100 (%) |

### Actionneurs (actuators)

Format : `campus/orion/{ROOM}/actuators/{TYPE}`

| Topic | Description | Valeurs |
|-------|-------------|---------|
| `.../actuators/motor` | Commande moteur | 0-100, open, close |
| `.../actuators/motor/position` | Position actuelle | 0-100 |
| `.../actuators/speaker` | Commande buzzer | beep, warning, danger, co2, stop |
| `.../actuators/speaker/active` | État actif | 0 ou 1 |

## Câblage

### Gateway (Arduino + XBee)

| XBee | Arduino UNO R4 |
|------|----------------|
| VCC | 5V |
| GND | GND |
| DOUT (TX) | D0 (RX) |
| DIN (RX) | D1 (TX) |

### BME280 (Température/Humidité)

| BME280 | Arduino |
|--------|---------|
| VCC | **3.3V** (pas 5V!) |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

### HC-SR04 (Présence)

| HC-SR04 | Arduino |
|---------|---------|
| VCC | 5V |
| GND | GND |
| TRIG | D8 |
| ECHO | D9 |

### Potentiomètre

| Potentiomètre | Arduino |
|---------------|---------|
| Pin gauche | GND |
| Pin milieu (wiper) | A0 |
| Pin droite | 5V |

### Servo Motor (HTEC HS-905BB+)

| Servo | Arduino |
|-------|---------|
| Signal (orange/jaune) | D9 (PWM) |
| VCC (rouge) | 5V (ou alim externe) |
| GND (marron/noir) | GND |

### Buzzer/Speaker

| Buzzer | Arduino |
|--------|---------|
| + | D10 (PWM) |
| - | GND |

## Configuration par capteur

Dans chaque fichier `.ino`, modifier ces constantes :

```cpp
const char* DEVICE_ID = "bme280_001";  // ID unique
const char* ROOM = "X101";              // Salle
const char* BUILDING = "orion";         // Bâtiment
```

## Dépannage

### Le bridge ne se connecte pas à MQTT

```bash
# Vérifier que Docker tourne
docker ps | grep mosquitto

# Tester la connexion MQTT
docker exec campus-mosquitto mosquitto_pub -t test -m "hello"
```

### Le bridge ne trouve pas le port série

1. Débrancher/rebrancher l'Arduino
2. Vérifier le port : `ls /dev/cu.usb*`
3. Fermer Arduino IDE (conflit de port)

### Pas de données reçues du XBee

1. Vérifier le câblage TX/RX (inversé entre émetteur et récepteur)
2. Vérifier que les XBee sont sur le même canal/PAN ID
3. Vérifier le baud rate (9600 par défaut)

### Le moteur ne bouge pas

1. Vérifier l'alimentation (servo peut nécessiter alim externe)
2. Vérifier la connexion PWM (D9)
3. Tester avec commande directe : `motor 50`

### Le buzzer ne sonne pas

1. Vérifier la polarité (+/-)
2. Vérifier la connexion PWM (D10)
3. Tester avec : `speaker test`

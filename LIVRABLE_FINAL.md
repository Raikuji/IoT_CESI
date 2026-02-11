# LIVRABLE FINAL - Projet IoT Campus CESI Nancy
## Réseau de capteurs sans fil ZigBee avec supervision MQTT

**Date** : 11 février 2026  
**Projet** : Système de monitoring environnemental par réseau de capteurs IoT
**Établissement** : CESI Nancy  
**Dépôt Git** : https://github.com/Raikuji/IoT_CESI

## Sommaire

Ce livrable contient les éléments suivants conformément aux exigences :

### 1. [CODE DU PROJET (commenté)](#1-code-du-projet-commenté)
   - Code Arduino Gateway Coordinator
   - Code Arduino End Device
   - Code Bridge MQTT Python
   - Bibliothèques de sécurité HMAC

### 2. [ARCHITECTURE IoT COMPLÈTE](#2-architecture-iot-complète)
   - Schéma d'architecture de la chaîne IoT
   - Schéma électrique détaillé
   - Justification des choix techniques
   - Limites et performances attendues

### 3. [DOCUMENTATION UTILISATEUR](#3-documentation-utilisateur)
   - Guide d'installation hardware
   - Guide de configuration XBee
   - Guide d'utilisation et supervision
   - Guide de dépannage

# 1. CODE DU PROJET (commenté)

**Dépôt GitHub** : https://github.com/Raikuji/IoT_CESI

Le code source complet du projet est disponible sur le dépôt GitHub ci-dessus. Il contient :

## Structure du code

```
campus-iot/firmware/
├── gateway/
│   ├── gateway.ino              # Arduino Mega Coordinator (commenté)
│   └── mqtt_bridge.py           # Bridge Python MQTT (commenté)
├── transmitter_bme280/
│   └── transmitter_bme280.ino   # End Device capteur température
├── transmitter_ultrasonic/
│   └── transmitter_ultrasonic.ino # End Device capteur présence
├── transmitter_potentiometer/
│   └── transmitter_potentiometer.ino # End Device CO2 simulé
├── actuator_motor/
│   └── actuator_motor.ino       # Test moteur standalone
├── actuator_speaker/
│   └── actuator_speaker.ino     # Test buzzer standalone
└── lib/
    └── hmac_security.h          # Bibliothèque HMAC-SHA256
```

## Fichiers principaux

### 1.1 Gateway Coordinator (`gateway.ino`)
- **Rôle** : Coordinateur ZigBee central
- **Fonctions** :
  - Lecture capteurs locaux (BME280, HC-SR04, potentiomètre)
  - Réception données End Devices via XBee
  - Formatage JSON avec authentification HMAC
  - Envoi via Serial USB vers Bridge Python
  - Contrôle actionneurs (moteur DC, buzzer)
- **Lignes de code** : ~350 lignes commentées

### 1.2 End Device (`transmitter_bme280.ino`)
- **Rôle** : Nœud capteur autonome
- **Fonctions** :
  - Lecture BME280 (température, humidité, pression)
  - Formatage JSON + HMAC
  - Transmission ZigBee vers Coordinator
- **Lignes de code** : ~100 lignes commentées

### 1.3 Bridge MQTT (`mqtt_bridge.py`)
- **Rôle** : Passerelle IoT ↔ IT
- **Fonctions** :
  - Lecture série USB depuis Arduino
  - Validation HMAC
  - Publication MQTT (QoS 1, retained)
  - Souscription commandes actionneurs
  - Reconnexion automatique
- **Lignes de code** : ~200 lignes commentées

### 1.4 Bibliothèque sécurité (`hmac_security.h`)
- **Rôle** : Authentification messages ZigBee
- **Algorithme** : HMAC-SHA256
- **Fonction principale** : `String computeHMAC(payload, secret)`
- **Usage** : Protection contre spoofing et corruption

## Installation du code

```bash
# Cloner le dépôt
git clone https://github.com/Raikuji/IoT_CESI.git
cd IoT_CESI/campus-iot/firmware

# Compiler et flasher Arduino (via Arduino IDE)
# Fichier → Ouvrir → gateway/gateway.ino
# Outils → Carte → Arduino Mega 2560
# Outils → Port → /dev/ttyACM0
# Croquis → Téléverser

# Installer dépendances Python Bridge
pip install pyserial paho-mqtt

# Lancer le bridge
python gateway/mqtt_bridge.py
```

## Commentaires et documentation

Tous les fichiers `.ino` et `.py` contiennent :
- **En-tête** : Description, auteur, date, matériel
- **Commentaires de fonctions** : Paramètres, return, usage
- **Commentaires inline** : Explication logique complexe
- **Constantes documentées** : Pins, timings, adresses

## Architecture complète de la chaîne IoT

### Vue d'ensemble du système

Le projet consiste en un **réseau de capteurs sans fil** déployé dans le bâtiment Orion du campus CESI Nancy. L'objectif est de collecter des données environnementales (température, humidité, pression, présence, CO2) via des capteurs autonomes communiquant en ZigBee, et de centraliser ces données via un protocole MQTT pour supervision et contrôle d'actionneurs.

### Schéma d'architecture matérielle

```
┌─────────────────────────────────────────────────────────────────────┐
│                   COUCHE CAPTEURS (End Devices)                     │
├─────────────────────────────────────────────────────────────────────┤
│  NŒUD 1: Salle X101                                                 │
│  ├─ BME280: Temp/Humid/Press (I2C 0x76)                             │
│  ├─ HC-SR04: Présence ultrason (GPIO Trig/Echo)                     │
│  ├─ Potentiomètre: CO2 simulé (ADC A0, 0-1023 → 0-2000 ppm)        │
│  └─ Arduino UNO + XBee End Device                                   │
│                                                                      │
│  NŒUD 2: Salle X102                                                 │
│  ├─ BME280: Temp/Humid/Press                                        │
│  ├─ MQ-135: CO2 réel (ADC A1, calibration requis)                   │
│  └─ Arduino UNO + XBee End Device                                   │
│                                                                      │
│  NŒUD N: Extensible jusqu'à 65 000 nœuds (limite théorique ZigBee) │
│  Alimentation: USB 5V ou batterie Li-Ion 3.7V (autonomie ~7j)       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ ZigBee Mesh Network (IEEE 802.15.4)
                             │ • Fréquence: 2.4 GHz (Canal 15)
                             │ • Débit: 250 kbps
                             │ • Portée: ~30m indoor / ~100m outdoor
                             │ • Topologie: Mesh auto-cicatrisante
                             │ • Sécurité: HMAC-SHA256 sur payload
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                  GATEWAY COORDINATOR (Hub Central)                  │
├─────────────────────────────────────────────────────────────────────┤
│  HARDWARE:                                                           │
│  ├─ Arduino Mega 2560 (16 MHz, 256KB Flash, 8KB RAM)               │
│  ├─ XBee Series 2 Coordinator (Module ZigBee coordinateur)          │
│  ├─ Shield XBee officiel Digi (Serial UART mapping)                 │
│  └─ Capteurs locaux (identiques aux End Devices)                    │
│                                                                      │
│  ACTIONNEURS INTÉGRÉS:                                               │
│  ├─ Moteur DC 12V (Ventilation/Volets)                              │
│  │  └─ Pilotage: PWM Pin 5 → Driver L298N → Relay                  │
│  └─ Buzzer piézo/Speaker (Alarme sonore)                            │
│     └─ Pilotage: PWM Pin 6 → Transistor NPN                         │
│                                                                      │
│  RÔLE:                                                               │
│  • Agréger les données des End Devices via XBee                     │
│  • Lire les capteurs locaux via I2C/GPIO/ADC                        │
│  • Formater les données en JSON                                     │
│  • Envoyer via liaison série USB à la Gateway Application           │
│  • Recevoir commandes actionneurs depuis Gateway Application        │
│                                                                      │
│  PROTOCOLE SÉRIE:                                                    │
│  • Baud rate: 9600 baud                                             │
│  • Format: JSON sur ligne unique terminée par \n                    │
│  • Exemple émis: {"room":"X101","type":"temp","value":23.5,"ts":..} │
│  • Exemple reçu: {"cmd":"motor","value":150}                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Liaison série USB (UART)
                             │ • Port: /dev/ttyACM0 (Linux) ou COM3 (Win)
                             │ • 9600 baud, 8N1
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│               GATEWAY APPLICATION (Bridge IoT ↔ IT)                 │
├─────────────────────────────────────────────────────────────────────┤
│  PLATEFORME: PC/Raspberry Pi sous Linux/Windows                     │
│                                                                      │
│  LOGICIEL: mqtt_bridge.py (Python 3.10+)                            │
│  ├─ Dépendances: pyserial, paho-mqtt                                │
│  ├─ Lecture série asynchrone (buffer ligne)                         │
│  ├─ Parse JSON et validation                                        │
│  ├─ Publication MQTT sur topics structurés                          │
│  └─ Souscription MQTT pour commandes actionneurs                    │
│                                                                      │
│  FONCTIONNALITÉS:                                                    │
│  • Parsing des trames capteurs → Publish MQTT                       │
│  • Écoute topics actionneurs → Envoi série Arduino                  │
│  • Gestion erreurs: reconnexion auto, buffer overflow               │
│  • Logs horodatés (stdout + fichier optionnel)                      │
│  • CLI interactive: commandes manuelles moteur/speaker              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ MQTT over TCP/IP
                             │ • Port: 1883 (TCP) ou 8883 (TLS/SSL)
                             │ • QoS: 1 (at least once delivery)
                             │ • Protocol: MQTT v3.1.1
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    BROKER MQTT (Message Hub)                        │
├─────────────────────────────────────────────────────────────────────┤
│  LOGICIEL: Eclipse Mosquitto 2.0                                    │
│  • Conteneurisé: Docker image officielle                            │
│  • Persistance: Volume Docker pour QoS/Retained messages            │
│  • Authentification: Username/Password (fichier passwd)             │
│  • Chiffrement: TLS/SSL optionnel (certificats Let's Encrypt)       │
│                                                                      │
│  TOPICS MQTT (Hiérarchie):                                          │
│  • campus/orion/sensors/temperature    → Données temp               │
│  • campus/orion/sensors/humidity       → Données humid              │
│  • campus/orion/sensors/pressure       → Données press              │
│  • campus/orion/sensors/co2            → Données CO2                │
│  • campus/orion/sensors/distance       → Présence ultrason          │
│  • campus/orion/actuators/motor        → Commandes moteur           │
│  • campus/orion/actuators/speaker      → Commandes alarme           │
│  • campus/orion/system/status          → Heartbeat/santé système    │
│                                                                      │
│  PORTS:                                                              │
│  • 1883: MQTT TCP (backend + bridge)                                │
│  • 9001: MQTT WebSocket (frontend temps réel)                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
    Subscription                           WebSocket (optionnel)
        │                                         │
┌───────▼──────────────────┐    ┌────────────────▼──────────────────┐
│   BACKEND API            │    │  SUPERVISION WEB (Dashboard)      │
│   (Persistance)          │    │  (Optionnel - Interface humaine)  │
├──────────────────────────┤    ├───────────────────────────────────┤
│ • FastAPI (Python)       │    │ • Vue.js 3 SPA                    │
│ • Client MQTT async      │    │ • Connexion MQTT WebSocket        │
│ • Stockage PostgreSQL    │    │ • Graphiques temps réel           │
│ • TimescaleDB extension  │    │ • Contrôle actionneurs manuel     │
│ • Endpoints REST         │    │ • Visualisation historiques       │
└──────────────────────────┘    └───────────────────────────────────┘
```

### Flux de données détaillé

#### Scénario 1 : Mesure capteur → Supervision

```
┌──────────┐
│ Capteur  │ BME280 mesure température = 23.5°C
│ BME280   │ ↓
└─────┬────┘ Lecture I2C par Arduino (Wire.begin(), 0x76)
      │      ↓
┌─────▼────┐ Arduino End Device formate:
│ Arduino  │ {"room":"X101","type":"temp","value":23.5,"ts":1707645600}
│ + XBee   │ ↓
└─────┬────┘ Transmission ZigBee (Broadcast vers Coordinator)
      │      • Payload: ~60 bytes
      │      • Latence: ~50-100ms (mesh hop count × 20ms)
      │      ↓
┌─────▼────────┐
│ Coordinator  │ XBee Coordinator reçoit trame ZigBee
│ Arduino Mega │ ↓
└─────┬────────┘ Arduino Mega transfère via Serial.println()
      │          ↓
┌─────▼──────────┐
│ mqtt_bridge.py │ Lecture ligne série (readline() bloquant)
│ (Python)       │ ↓
└─────┬──────────┘ Parse JSON, validation, ajout métadonnées
      │            ↓
┌─────▼────────┐
│ Mosquitto    │ Publish sur "campus/orion/sensors/temperature"
│ (MQTT Broker)│ • QoS 1 (garantie livraison)
└─────┬────────┘ • Retained message (dernier état disponible)
      │          ↓
      ├──────────→ Backend subscribes → Stockage BDD (historique)
      │          ↓
      └──────────→ Frontend WebSocket → Affichage Dashboard live

Latence totale estimée: 200-500 ms (bout en bout)
```

#### Scénario 2 : Commande actionneur

```
┌───────────┐
│ Utilisateur│ Clique "Démarrer moteur vitesse 150"
└─────┬─────┘
      │ HTTP POST /api/actuators/motor {"value":150}
      ↓
┌─────▼────────┐
│ Backend API  │ Validation + Log + Publish MQTT
└─────┬────────┘ → Topic: "campus/orion/actuators/motor"
      │          → Payload: {"room":"X101","value":150}
      ↓
┌─────▼────────┐
│ Mosquitto    │ Broadcast vers subscribers
└─────┬────────┘
      │
┌─────▼──────────┐
│ mqtt_bridge.py │ Callback on_message() triggered
│                │ ↓
└─────┬──────────┘ Formate commande série: {"cmd":"motor","value":150}\n
      │            ↓
┌─────▼────────┐
│ Arduino Mega │ Serial.available() → parse JSON
│ Coordinator  │ ↓
└─────┬────────┘ analogWrite(MOTOR_PIN, 150); // PWM duty cycle
      │          ↓
┌─────▼────┐
│ Driver   │ L298N driver contrôle Relay → Moteur 12V tourne
│ L298N    │ • Vitesse proportionnelle: 150/255 ≈ 59% duty
└──────────┘

Latence totale estimée: 100-300 ms (clic → action physique)
```

### Schéma électrique simplifié (Gateway Coordinator)

```
                    Arduino Mega 2560
                   ┌─────────────────┐
                   │                 │
   BME280 ─────────┤ SDA(20) SCL(21) │ (I2C Bus)
   (0x76)          │                 │
                   │ A0 ←───────────┐│ Potentiomètre CO2 (0-1023)
                   │                 │
   HC-SR04         │ Pin 7 (Trig)    │
   Ultrasonic ─────┤ Pin 8 (Echo)    │
                   │                 │
                   │ Pin 5 (PWM) ────┼──→ L298N IN1 ──→ Relay ──→ Moteur 12V
                   │                 │
                   │ Pin 6 (PWM) ────┼──→ NPN Base ──→ Buzzer/Speaker
                   │                 │
   XBee Shield     │ Serial1 RX/TX   │ (XBee Coordinator)
                   │                 │
   USB ────────────┤ USB Port        │──→ PC/Raspberry (Serial 9600)
                   │                 │
   5V Adapter ─────┤ Vin (7-12V)     │ (Alimentation externe si actionneurs)
                   └─────────────────┘

Notes:
- XBee alimenté par shield (3.3V régulateur intégré)
- Moteur 12V nécessite alimentation externe (pas USB)
- Driver L298N isole logique 5V de puissance 12V
- Buzzer via transistor NPN pour amplification courant
```

## Justification des choix techniques IoT

### 1. **Microcontrôleurs : Arduino Mega 2560 vs Arduino UNO**

| Aspect | Arduino UNO | Arduino Mega 2560 | Choix final |
|--------|-------------|-------------------|-------------|
| **Mémoire Flash** | 32 KB | 256 KB | **Mega** : nécessaire pour XBee + capteurs + HMAC |
| **RAM** | 2 KB | 8 KB | **Mega** : évite overflow avec buffers JSON |
| **Ports série** | 1 (USB) | 4 (USB + 3 UART) | **Mega** : XBee sur Serial1, USB Serial0 |
| **Pins I2C** | 1 bus | 2 bus | **Mega** : un bus par End Device si extension |
| **Prix** | ~20€ | ~35€ | **Mega** : +15€ justifiés par capacités |
| **Compatibilité** | UNO pour End Devices simples | Mega pour Gateway | **Hybride** optimal |

**Décision** : Arduino Mega 2560 pour Gateway Coordinator, Arduino UNO pour End Devices simples (économie).

### 2. **Capteurs : Choix et justifications**

#### BME280 (Température/Humidité/Pression)

| Critère | BME280 | DHT22 | Justification |
|---------|--------|-------|---------------|
| **Précision temp** | ±0.5°C | ±0.5°C | Équivalent |
| **Précision humid** | ±3% HR | ±2% HR | DHT légèrement meilleur |
| **Interface** | I2C/SPI | 1-Wire | **BME280** : I2C = multi-capteurs même bus |
| **Consommation** | 3.6 µA idle | 0.15 mA idle | **BME280** : 40x moins consommateur |
| **Temps réponse** | 1 s | 2 s | **BME280** : 2x plus rapide |
| **Pression baro** | Oui (300-1100 hPa) | Non | **BME280** : 3-en-1 |
| **Prix** | ~8€ | ~5€ | **BME280** : +3€ pour 3 capteurs |

**Décision** : BME280 pour ratio précision/consommation/fonctionnalités.

#### HC-SR04 (Ultrasons présence/distance)

| Critère | HC-SR04 | PIR (infrarouge) | Justification |
|---------|---------|------------------|---------------|
| **Portée** | 2 cm - 4 m | 5-12 m | **HC-SR04** : distance précise (PIR binaire) |
| **Angle détection** | 15° (faisceau) | 110° (large) | **PIR** meilleur couverture |
| **Consommation** | 15 mA | 50 µA | **PIR** ultra-économe |
| **Faux positifs** | Rares (ultrason) | Fréquents (chaleur) | **HC-SR04** : plus fiable |
| **Prix** | ~2€ | ~3€ | **HC-SR04** : moins cher |
| **Donnée** | Distance (cm) | Booléen (présence/absence) | **HC-SR04** : plus riche |

**Décision** : HC-SR04 pour données de distance exploitables (comptage, occupation précise).

#### Potentiomètre vs MQ-135 (CO2)

| Critère | Potentiomètre | MQ-135 (réel) | Justification |
|---------|---------------|---------------|---------------|
| **Précision** | N/A (simulé) | ±50 ppm | **MQ-135** meilleur |
| **Calibration** | Aucune | Complexe (48h warm-up) | **Pot** : simple, rapide |
| **Consommation** | 0 mA | 150 mA (heating) | **Pot** : économique |
| **Prix** | ~1€ | ~5€ | **Pot** : 5x moins cher |
| **Temps réel** | Instantané | Délai 10-30 s | **Pot** : réactif |
| **MVP/Démo** | Suffisant | Overkill | **Pot** : adapté phase 1 |

**Décision** : Potentiomètre en phase 1 (MVP), migration vers MQ-135 en phase 2 si besoin réel.

### 3. **Communication sans fil : ZigBee (XBee Series 2)**

#### Comparaison protocoles IoT

| Protocole | Portée | Débit | Conso idle | Topologie | Coût module | Justification |
|-----------|--------|-------|------------|-----------|-------------|---------------|
| **ZigBee** | 30m / 100m | 250 kbps | 1 µA | Mesh | ~30€ | ✅ Optimal indoor |
| **WiFi 802.11** | 50m / 100m | 54 Mbps | 80 mA | Star | ~5€ | ❌ Trop gourmand |
| **LoRaWAN** | 2 km / 15 km | 0.3-50 kbps | 1.5 µA | Star | ~20€ | ❌ Trop lent |
| **Bluetooth Low Energy** | 10m / 50m | 1 Mbps | 1 µA | Star/Mesh | ~8€ | ❌ Portée limitée |
| **Z-Wave** | 30m / 100m | 100 kbps | 0.5 µA | Mesh | ~35€ | ❌ Propriétaire |
| **Thread** | 30m / 100m | 250 kbps | 1 µA | Mesh | ~25€ | ⚠️ Émergent |

**Pourquoi ZigBee gagne :**

1. **Mesh auto-cicatrisante** : Si un routeur tombe, le réseau se reconfigure automatiquement
2. **Consommation faible** : End Device en sleep mode = autonomie batterie ~7 jours
3. **Portée adaptée bâtiment** : 30m indoor avec murs béton, extensible via routeurs
4. **Débit suffisant** : 250 kbps >> nos besoins (~500 bits/msg × 1 msg/min = 8 bps)
5. **Standard industriel** : IEEE 802.15.4, bibliothèques Arduino matures
6. **Scalabilité** : Jusqu'à 65 000 nœuds par réseau (théorique)

**Pourquoi pas WiFi :**
- Consommation 80 mA idle vs 1 µA ZigBee = autonomie batterie impossible
- Bâtiments béton = atténuation excessive = dead zones
- Nécessite infrastructure (routeurs, DHCP) = coûts

**Pourquoi pas LoRaWAN :**
- Optimisé longue portée (km) = overkill pour bâtiment
- Débit trop faible (0.3 kbps) = latence excessive
- Topologie star = pas de résilience

### 4. **Communication locale : I2C vs SPI vs 1-Wire**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi Arduino Mega** | Microcontrôleur robuste + ports multiples | 2x port I2C, PWM, ADC, mémoire suffisante pour HMAC, prix abordable |
| **Pourquoi I2C** | Standard pour capteurs numériques | Consommation faible, 2 fils (SDA/SCL), adressage multiple, fiabilité |
| **Pourquoi GPIO analogique** | Capture du potentiomètre (CO2) | Conversion ADC 10-bit suffisante (~0.1V précision), simulation CO2 acceptable pour MVP |

#### 2. **Communication longue distance : ZigBee (XBee)**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi ZigBee** | Protocole mesh optimisé IoT | Auto-healing, portée ~30m indoor (extensible via routeurs), faible consommation, jusqu'à 65 000 nœuds supportés |
| **Pourquoi pas WiFi** | WiFi trop gourmand en puissance | Bâtiments en béton : atténuation excessive, mobilité réseau problématique, couts serveurs/AP élevés |
| **Pourquoi pas LoRaWAN** | LoRa trop lent/lointain pour cet usage | Designed pour longue portée/faible débit (agricole), pas adapté au temps réel local |
| **Portée effective** | ~30m indoor, ~300m outdoor | Suffit pour un bâtiment, extensible via routeurs ZigBee |
| **Sécurité XBee** | HMAC-SHA256 sur payload | Authentification sans surcharge crypto lourde, adapté aux contraintes Arduino |

#### 3. **Protocole applicatif : MQTT**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi MQTT** | Publish/Subscribe léger | Overhead minimal, QoS configurable (0/1/2), RETAIN pour état persistant, standard industriel |
| **Pourquoi pas HTTP/REST** | REST stateless = requête/réponse | Inefficace pour IoT (polling coûteux), MQTT permet subscriptions actives |
| **Pourquoi pas CoAP** | CoAP = constrained devices | Projet a serveur stable, MQTT plus standardisé en industrie |
| **Topics structurés** | `campus/orion/sensors/{type}` | Hiérarchie claire, subscriptions spécifiques par type, monitoring simple |

#### 4. **Broker MQTT : Mosquitto**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi Mosquitto** | Open source, léger, stable | <100 MB RAM, débit ~10k msg/s mono-serveur, WebSocket natif, config simple |
| **Pourquoi pas RabbitMQ** | RabbitMQ trop lourd (~500 MB) | Overkill pour cette charge, complexité de gestion |
| **Pourquoi pas EMQX** | EMQX premium > Mosquitto | Mosquitto gratuit et suffisant pour ~50 capteurs |
| **WebSocket support** | Mosquitto port 9001 | Frontend navigateur se connecte directement en WebSocket (pas de proxy NodeJS) |

#### 5. **Gateway application : Python script**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi Python** | Rapidité développement, écosystème riche | Libraries: `pyserial`, `paho-mqtt` disponibles, facile à maintenir |
| **Pourquoi pas C++** | C++ plus rapide mais moins maintenable | Gain perf marginal pour ce débit (quelques msg/sec), risque bugs mémoire |
| **Fonctionnalités** | Parse série, publie MQTT, reçoit commandes | Stateless, relancé automatiquement si crash |

#### 6. **Backend : FastAPI (Python)**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Async natif** | FastAPI vs Flask/Django | WebSocket + MQTT client simultanés sans threading complexe, perfs ~10x meilleures |
| **Validation** | Pydantic schemas | Validation auto des entrées, génération docs Swagger, erreurs claires |
| **ORM** | SQLAlchemy 2.0 | Protection injection SQL native, migrations avec Alembic, requêtes complexes faciles |
| **Auth JWT** | Tokens stateless | Scalable multi-instance, expiration configurable, standard industrie |
| **Documentatio** | Auto-génération Swagger | `/docs` : API interactive, économise temps doc manuelle |

#### 7. **Base de données : PostgreSQL + TimescaleDB**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi PostgreSQL** | SGBD robuste, open-source | ACID complet, transactions, indexation performante, cloud hosting fiable (Supabase) |
| **TimescaleDB** | Extension PostgreSQL pour time-series | Compression automatique (90% des données), requêtes rapides sur chroniques, gestion rétention simple |
| **Pourquoi pas InfluxDB** | InfluxDB moins flexible | Optimisé time-series pur, mais moins adapté aux logs utilisateurs/audit |
| **Cloud (Supabase)** | Pas de gestion infra | Backups auto, uptime 99.9%, scaling transparent, couts réduits |

#### 8. **Frontend : Vue 3 + Vuetify**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Vue 3** | Réactivité native | Two-way binding, SPA performante, écosystème complet (Router, Pinia) |
| **Pourquoi pas React** | React + TypeScript plus verbeux | Vue plus simple pour équipe junior, output identique |
| **Vuetify** | Composants Material Design | Pre-faits, responsive, cohérence UI, icons intégrés |
| **WebSocket direct** | Frontend → Mosquitto WS | Pas de backend relai, notifications live sans latence, scalable |

#### 9. **Déploiement : Docker Compose**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi Docker** | Reproductibilité, isolation | Même config dev/prod, pas "marche chez moi", services indépendants |
| **Compose vs Kubernetes** | Compose = simple node unique | Kubernetes overkill, Compose suffisant pour 1 serveur stable |
| **Volumes** | Données persistantes | BDD/MQTT logs sauvegardés entre redémarrages |

---

## Limites et performances attendues

### Performances nominales

| Critère | Valeur | Détail |
|---------|--------|--------|
| **Latence capteur → dashboard** | < 2 s | XBee (~50ms) + MQTT (~100ms) + WebSocket (~50ms) + rendu UI (~800ms) |
| **Latence API → actionneur** | < 1 s | REST parse (~50ms) + MQTT pub (~100ms) + Arduino serial (~100ms) + relay (~700ms) |
| **Débit XBee** | 250 kbps | Suffisant pour ~50 capteurs à 60s intervalle (~500 bits/msg) |
| **Capacité MQTT** | ~10 000 msg/s | Mosquitto mono-serveur, bien au-dessus de nos besoins (~1 msg/s réel) |
| **Connexions WebSocket simultanées** | ~50 utilisateurs | Limité par FastAPI async workers (4–8 default), extensible |
| **Stockage BDD/an** | ~100 Mo | Estimé: 10 capteurs × 52 560 mesures/an (60s intervalle) × 20 bytes/mesure = 10.5 Mo base; logs/alertes ~90 Mo |
| **Temps de réponse API** | < 200 ms | FastAPI async, requête simple en ~20-50 ms, complexe ~100-150 ms |
| **Disponibilité** | ~99% (hors maintenance) | Docker restart auto, ~10 min SLA maintenance hebdo |

### Limites architecturales identifiées

#### 1. **Pas de redondance (single-node)**

- **Impact** : Si le serveur tombe, plus de monitoring
- **Raison** : Bâtiment unique, coûts doublés unjustifiés pour cette phase
- **Mitigation** : Backups automatiques (Supabase), alertes email sur arrêt

#### 2. **Portée XBee limitée à ~30m indoor**

- **Impact** : Grand bâtiment (>50m) nécessite routeurs ZigBee
- **Raison** : Atténuation béton/métal, 250 kbps limite portée
- **Mitigation** : Ajouter routeurs XBee (coût ~80€/unité), maillage auto-guérison

#### 3. **Authentification et chiffrement MQTT**

- **Statut** : Implémenté
- **Implémentation** : TLS/SSL + username/password sur Mosquitto
- **Sécurité** : Communication chiffrée (port 8883), authentification par topic ACL
- **Performance** : Latence additionnelle < 5ms, acceptable

#### 4. **Alimentation des capteurs (USB/secteur, pas de batterie)**

- **Impact** : Capteurs fixes, pas de mobilité
- **Raison** : Bâtiment intelligent = infrastructure permanente, maintenance acceptable
- **Mitigation** : UPS sur gateway Arduino pour continuité lors coupure secteur

#### 5. **Pas de buffer local si broker/backend tombe**

- **Impact** : Mesures perdues si Mosquitto ou FastAPI offline
- **Raison** : Bridge Python stateless, Arduino n'a pas mémoire pour buffer
- **Mitigation** : Broker/Backend très stable en Docker, restart auto < 1 min

#### 6. **Scalabilité limitée à 1 bâtiment**

- **Impact** : Ajout nouveau bâtiment = nouvelle instance (pas de multi-tenant)
- **Raison** : Architecture simple, pas de complexité cloud au stade MVP
- **Mitigation** : Refactoring futur avec namespace prefix: `campus/orion/` vs `campus/batiment2/`

#### 7. **Nombre de capteurs directs limité (~20-30)**

- **Impact** : Plus de capteurs = dégradation perfs ZigBee
- **Raison** : Coordinateur XBee a limite nœuds directs
- **Mitigation** : Ajouter routeurs XBee (gratuit topologiquement, ~80€ par routeur)

### Optimisations possibles (future)

| Optimisation | Effort | Bénéfice |
|--------------|--------|----------|
| TLS sur MQTT | Facile | Sécurité réseau +++ |
| Clustering PostgreSQL | Moyen | Haute dispo ++ |
| Horizontale API (load balancer) | Moyen | Scalabilité +++ |
| Cache Redis (sessions/métriques) | Moyen | Perf API ++ |
| Compaction TimescaleDB (30 jours) | Facile | Stockage -80% |
| Routeurs ZigBee (relai) | Facile | Portée +++ |
| Backup crypto (Supabase) | Facile | Sécurité données ++ |

---

## 👤 Guide utilisateur - Administrateur

### 1. Accès administration

```
URL: http://localhost/admin
Identifiants: admin@cesi.fr / admin123 (par défaut)
CHANGER le mot de passe initial immédiatement
```

### 2. Première connexion - Setup initial

1. **Créer les utilisateurs**
   - Aller à: Administration → Gestion utilisateurs
   - Cliquer "Ajouter un utilisateur"
   - Remplir email, prénom, nom, rôle
   - Rôles disponibles:
     - **Admin** : Accès complet, gestion utilisateurs
     - **Technicien** : Gestion capteurs, actionneurs, alertes
     - **Responsable** : Consultation avancée, export données
     - **Utilisateur** : Lecture seule dashboard

2. **Placer les capteurs**
   - Aller à: Bâtiment Orion → Salles
   - Cliquer sur une salle (ex: X101)
   - "Placer un capteur" → Sélectionner capteur physique (ex: BME280_01)
   - Configurer:
     - Type: Temperature, Humidity, CO2, Presence, Light, Pressure
     - Topic MQTT: `campus/orion/sensors/{type}`
     - Intervalle: 60 sec (normal), 120 sec (éco), 300 sec (nuit)

3. **Configurer les profils énergie**
   - Par capteur:
     - Normal (100%): Acquisition 60s, live activé
     - Éco (60%): Acquisition 120s, live désactivé
     - Nuit (40%): Acquisition 300s, live désactivé
   - Planning: Activer/désactiver automatiquement par jour/heure

4. **Configurer les alertes**
   - Aller à: Alertes → Règles
   - Créer règle: Seuil temp > 28°C → Sévérité "warning"
   - Notifications: Email + notifications live

5. **Tester le système**
   - Dashboard: Vérifier affichage données temps réel
   - Créer alerte test
   - Tester actionneur moteur (Contrôle → Moteur → Vitesse 150)

### 3. Gestion quotidienne

**Accueil Admin:**
- Utilisateurs actifs (count)
- Capteurs en ligne (count)
- Alertes non résolues
- Taux d'activité capteurs (% en mode normal/éco/nuit)

**Tâches courantes:**
- Consulter journal d'activité (qui a modifié quoi)
- Acquitter/résoudre alertes critiques
- Activer/désactiver utilisateurs
- Exporter rapports (Rapports → Export CSV/JSON)

### 4. Maintenance

**Hebdomadaire:**
- Vérifier "Capteurs inactifs" (Dashboard)
- Consulter "Erreurs API" (Logs)

**Mensuel:**
- Archiver les alertes résolues
- Exporter rapport consommation énergie
- Vérifier stockage BDD (Stockage: ~30 MB/mois)

**Semestriel:**
- Compaction TimescaleDB (Maintenance → Compress)
- Revue des rôles utilisateurs

### 5. Dépannage admin

| Problème | Cause probable | Solution |
|----------|----------------|----------|
| Pas de données temps réel | Bridge MQTT pas lancé | Vérifier: `docker ps` ou relancer manuelment |
| Alertes ne se créent pas | Règles mal configurées | Vérifier seuils dans Alertes → Règles |
| Utilisateur non reçoit pas email | SMTP non configuré | Vérifier `.env`: SMTP_SERVER, SMTP_PORT |
| Moteur ne répond pas | Relay hors ligne | Tester série Arduino, vérifier alimention relay |

---

## 👨‍💼 Guide utilisateur - Usager standard

### 1. Accès usager

```
URL: http://localhost
Identifiants: fournis par admin
Rôle: "Utilisateur" = lecture seule
```

### 2. Dashboard principal

**Vue par défaut: Salles et capteurs temps réel**

1. **Cartes salles** (X101, X102, X103...)
   - Température actuelle (fond couleur: vert/orange/rouge selon seuil)
   - Humidité (%)
   - Indicateur "En ligne" (vert) / "Inactif" (gris)
   - Clic sur carte → Détail salle

2. **Indicateurs clés (haut de page)**
   - Capteurs actifs: 18/20
   - Mode éco activé: 2 capteurs
   - Alertes non résolues: 1
   - Temp moyenne: 22.5°C

3. **Graphiques (bas de page)**
   - Température (courbe 24h)
   - Humidité (courbe 24h)
   - Sélecteur: 1h / 6h / 24h

### 3. Détail d'une salle

Cliquer sur une salle (X101) affiche:

- **Capteurs de la salle:**
  - Température: 23.5°C (dernier update: 2 min)
  - Humidité: 45% (dernier update: 2 min)
  - Pression: 1013 hPa
  - Statut: "En ligne"

- **Historique (picker date):**
  - Température min/max/moy jour
  - Graphique détaillé 24h

- **Alertes liées:**
  - "Temp élevée" - Warning - 10 min - Pas résolue
  - "Humidité basse" - Info - 1 h - Résolue

### 4. Alertes

Aller à: **Alertes** (menu)

- Liste des alertes actives (filtre: non résolues)
- Par alerte:
  - Salle concernée
  - Sévérité (info / warning / danger)
  - Message: "Température > 28°C"
  - Heure création / résolution

**Actions usager:**
- Cliquer alerte → Voir contexte (courbes temps réel)
- Pas de droit de résoudre (admin/technicien uniquement)

### 5. Rapports & Export

Aller à: **Rapports** (menu, visible si rôle "Responsable" ou "Admin")

- Sélectionner plage date (date début, date fin)
- Sélectionner salles (multi-select)
- Sélectionner métriques (Temp moy/min/max, Humidité, etc)
- Format export: CSV / JSON / PDF
- Cliquer "Télécharger"

**Exemple CSV:**
```
date,salle,temp_moy,hum_moy,alerts_count
2026-02-10,X101,22.5,45,0
2026-02-10,X102,21.8,48,1
...
```

### 6. Mode sombre / Préférences

Cliquer sur profil (haut droit) → Préférences

- Mode sombre (activé/désactivé)
- Unités: Celsius/Fahrenheit, %HR/%
- Langue: FR/EN
- Notifications push: activé/désactivé

### 7. Déconnexion

Cliquer profil (haut droit) → Déconnexion

## Guide utilisateur - IoT & Hardware

### 1. Composants et câblage

#### Gateway Arduino Mega

```
Arduino Mega 2560
├─ Port USB → PC (Serial 9600 baud)
├─ Port I2C (SDA=20, SCL=21)
│  └─ BME280 VCC/GND/SDA/SCL
├─ Port GPIO
│  ├─ Pin 7 = HC-SR04 TRIG
│  ├─ Pin 8 = HC-SR04 ECHO
│  ├─ Pin 5 = Moteur PWM (relay)
│  └─ Pin 6 = Speaker PWM (driver audio)
├─ Port ADC
│  └─ A0 = Potentiomètre CO2 (0-1023 = 0-500 ppm simulé)
└─ Shield XBee
   └─ XBee Coordinator (PAN ID: 1234, Channel: 15)
```

#### Capteurs distants (XBee)

```
Chaque capteur distant via XBee End Device:
├─ XBee Series 2 (End Device/Router)
├─ BME280 sur I2C local
└─ Alimenté 5V (USB/batterie)
```

### 2. Installation et configuration initiale

#### Étape 1 : Flasher l'Arduino

```bash
# Linux/macOS
cd campus-iot/firmware/gateway
# 1. Brancher Arduino au PC en USB
# 2. Ouvrir Arduino IDE
# 3. Fichier → Ouvrir → gateway.ino
# 4. Outil → Carte → Arduino Mega 2560
# 5. Outil → Port → /dev/ttyACM0 (ou COM3 sur Windows)
# 6. Croquis → Téléverser
# ✓ Compilation OK + Upload OK = succès
```

**Code gateway.ino teste les capteurs sur startup:**
```
SERIAL OUTPUT:
Initializing BME280... OK
Initializing HC-SR04... OK
Initializing ADC... OK
Initializing XBee... OK
System ready. Awaiting data...
```

#### Étape 2 : Configurer les XBees (XCTU)

```bash
# Télécharger XCTU (Digi)
# 1. Brancher Arduino + XBee au PC
# 2. Lancer XCTU
# 3. Add Device → Arduino port
# 4. Charger Firmware: Coordinator (sur gateway)
# 5. Configurer:
#    - PAN ID: 1234
#    - Channel: 15
#    - DL: 0x0000 (broadcast)
#    - Write
# 6. Vérifier Network Viewer: Coordinator visible, vert

# Répéter pour chaque XBee End Device:
# 4. Charger Firmware: End Device or Router
# 5. Configurer:
#    - PAN ID: 1234 (IDENTIQUE)
#    - Channel: 15 (IDENTIQUE)
#    - DL: 0x0000
#    - Write
# 6. Network Viewer: End Device joins network (peut prendre 30 sec)
```

#### Étape 3 : Lancer le Bridge Python

```bash
# Terminal 1: Lancer le bridge MQTT
cd campus-iot/firmware/gateway
python mqtt_bridge.py

# Output attendu:
# Connected to serial port /dev/ttyACM0 @ 9600 baud
# Connected to MQTT broker at localhost:1883
# Topics: campus/orion/sensors/*
# Ready for commands. Type 'help' for list.
```

#### Étape 4 : Vérifier le flux MQTT

```bash
# Terminal 2: S'abonner aux capteurs
mosquitto_sub -h localhost -p 1883 -t "campus/orion/sensors/#" -v

# Vous devriez voir:
# campus/orion/sensors/temperature {"room": "X101", "value": 23.5, "ts": 1707478234}
# campus/orion/sensors/humidity {"room": "X101", "value": 45.2, "ts": 1707478234}
# campus/orion/sensors/temperature {"room": "X102", "value": 22.1, "ts": 1707478236}
```

### 3. Commandes interactives (Bridge Python)

Une fois le bridge lancé:

```bash
# Afficher l'aide
> help

# Lire capteurs locaux
> temp              → Affiche: Temperature: 23.5°C
> hum               → Affiche: Humidity: 45.2%
> press             → Affiche: Pressure: 1013 hPa
> dist              → Affiche: Distance: 123 cm (ou "No object")

# Contrôler actionneurs
> motor 150         → Moteur vitesse 150/255 (0=off, 255=max)
> motor 0           → Arrêter moteur
> speaker 1         → Alarme sonore ON
> speaker 0         → Alarme sonore OFF

# Publier un message MQTT directement
> pub X101 temp 22.5          → Publie sur campus/orion/sensors/temperature
> pub X102 hum 48.0           → Publie sur campus/orion/sensors/humidity
> pub X103 co2 550            → Publie sur campus/orion/sensors/co2

# Récupérer un capteur distant (via XBee)
> xbee request temp           → Envoie requête au prochain XBee qui répond
> xbee request hum

# Autres
> status            → État global (capteurs, MQTT, XBee)
> exit              → Quitter le bridge
```

### 4. Tests et validation

#### Test 1 : Liaison série

```bash
# Vérifier que l'Arduino est vu
ls -la /dev/ttyACM* 

# Lancer un terminal série
screen /dev/ttyACM0 9600

# Vous devriez voir les logs Arduino
# Appuyer sur Ctrl+A, K, Y pour quitter
```

#### Test 2 : XBee maillage

```bash
# Lancer XCTU Network Viewer
# 1. Ajouter le port Arduino (Coordinator)
# 2. Onglet Network Viewer
# 3. Vous devriez voir:
#    - Coordinator au centre (vert)
#    - End Devices qui rejoignent le réseau (peut prendre 30 sec)
#    - Indicateurs force signal par lien
```

#### Test 3 : MQTT flux

```bash
# Terminal 1
cd campus-iot/firmware/gateway
python mqtt_bridge.py

# Terminal 2
mosquitto_sub -h localhost -p 1883 -t "campus/orion/#" -v

# Terminal 3: Publier une commande moteur
mosquitto_pub -h localhost -p 1883 \
  -t "campus/orion/actuators/motor" \
  -m '{"room": "X101", "value": 200}'

# Terminal 1: Vous devriez voir
# Received MQTT: campus/orion/actuators/motor
# Sending to Arduino: motor 200
# ✓ Moteur devrait tourner
```

#### Test 4 : API → Actionneur

```bash
# Via terminal ou Postman
curl -X POST http://localhost:8000/api/actuators/motor/command \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"room_id": "X101", "value": 150}'

# Réponse attendue:
# {"status": "ok", "message": "Motor command sent"}
```

#### Test 5 : Dashboard temps réel

```bash
# 1. Ouvrir http://localhost
# 2. Aller au Dashboard
# 3. Vous devriez voir les salles avec données temps réel
# 4. Ouvrir console navigateur (F12 → Console)
# 5. Vous devriez voir:
#    WebSocket connected
#    Message: {"type": "sensor_update", "data": {...}}
```

### 5. Dépannage IoT

| Problème | Cause | Solution |
|----------|-------|----------|
| **Pas de données série** | Arduino pas flashé | Re-flasher gateway.ino, vérifier port et baud rate (9600) |
| **Serial timeout** | Port USB débranché | Vérifier câble USB, relancer bridge |
| **XBee n'a pas d'adresse** | Pas de firmware | Recharger firmware Coordinator/End Device via XCTU |
| **End Device ne rejoint pas réseau** | PAN ID/Channel différent | Vérifier identiques entre Coordinator et End Devices |
| **Portée insuffisante (> 10 m)** | Obstacles béton/métal | Ajouter routeur XBee relai, placer Coordinator centralement |
| **MQTT pas connecté** | Mosquitto pas lancé | Vérifier: `docker ps` ou relancer `docker compose up` |
| **Pas de topics MQTT** | Bridge pas lancé | Lancer `python mqtt_bridge.py` |
| **Moteur ne démarre pas** | Relay pas alimenté | Vérifier 5V/GND sur relay, vérifier driver (BJT/Mosfet) |

### 6. Checklist déploiement

- [ ] Arduino Mega flashé avec gateway.ino
- [ ] XBee Coordinator sur le shield, port COM disponible
- [ ] XBee End Devices configurés (XCTU): PAN ID 1234, Channel 15
- [ ] Capteurs câblés: BME280 (I2C), HC-SR04 (GPIO 7/8), Potentiomètre CO2 (A0)
- [ ] Moteur/Speaker câblés: Relais (PWM 5), Speaker driver (PWM 6)
- [ ] Moniteur série: Messages OK sans erreur
- [ ] Bridge Python lancé: "Connected to MQTT broker"
- [ ] Mosquitto en ligne: `mosquitto_sub` reçoit les messages
- [ ] Backend FastAPI en ligne: `docker ps` montre conteneur "backend"
- [ ] Frontend Vue en ligne: http://localhost accessible
- [ ] Dashboard affiche données temps réel
- [ ] Actionneurs réagissent aux commandes


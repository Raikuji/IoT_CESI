# LIVRABLE FINAL - Projet IoT Campus CESI Nancy
## Réseau de capteurs sans fil ZigBee avec supervision MQTT

**Date** : 11 février 2026  
**Établissement** : CESI Nancy  
**Dépôt GitHub** : https://github.com/Raikuji/IoT_CESI

### Vue d'ensemble

Ce projet consiste en un système de monitoring environnemental pour le bâtiment Orion du campus CESI Nancy. On a mis en place un réseau de capteurs sans fil qui communiquent en ZigBee, avec un système de supervision MQTT pour visualiser les données en temps réel.

**Principales caractéristiques** :
- Réseau ZigBee mesh (portée environ 30m en intérieur, extensible avec des routeurs)
- Plusieurs types de capteurs : température, humidité, pression, présence et CO2
- Latence acceptable : moins de 500ms entre la mesure et l'affichage
- Sécurité des communications avec HMAC-SHA256
- Contrôle d'actionneurs à distance (moteur et alarme)

---

# 1. CODE DU PROJET

**Dépôt GitHub** : https://github.com/Raikuji/IoT_CESI

Tout le code source est disponible sur GitHub avec des commentaires pour faciliter la compréhension. Voici la structure principale :

```
firmware/
├── gateway/
│   ├── gateway.ino           # Arduino Mega Coordinator (350 lignes)
│   └── mqtt_bridge.py        # Bridge MQTT Python (200 lignes)
├── transmitter_bme280/       # End Device température
├── actuator_motor/           # Contrôle moteur
└── lib/hmac_security.h       # Sécurité HMAC-SHA256
```

**Composants principaux** :
- **Gateway Coordinator** : Collecte les données des capteurs, gère le réseau ZigBee et communique en USB avec le PC
- **End Devices** : Les capteurs autonomes (BME280 pour température/humidité, HC-SR04 pour la présence, potentiomètre pour le CO2)
- **Bridge Python** : Fait le lien entre la liaison série et MQTT, avec validation des messages
- **Bibliothèque HMAC** : Pour sécuriser les communications ZigBee

---

# 2. ARCHITECTURE IoT COMPLÈTE

## 2.1 Schéma d'architecture

```
┌─────────────────────────────────────────┐
│  CAPTEURS END DEVICES (Arduino + XBee)  │
│  • BME280 (Temp/Humid/Press) I2C       │
│  • HC-SR04 (Présence) GPIO             │
│  • Potentiomètre CO2 ADC               │
└──────────────┬──────────────────────────┘
               │ ZigBee Mesh (250 kbps, 30m indoor)
               │ • Auto-cicatrisation
               │ • HMAC-SHA256
               ↓
┌──────────────────────────────────────────┐
│  GATEWAY COORDINATOR (Arduino Mega)     │
│  • Réception ZigBee                     │
│  • Capteurs locaux                      │
│  • Actionneurs (Moteur DC, Buzzer)     │
│  • Formatage JSON + HMAC                │
└──────────────┬───────────────────────────┘
               │ Serial USB (9600 baud)
               ↓
┌──────────────────────────────────────────┐
│  BRIDGE PYTHON (mqtt_bridge.py)         │
│  • Parse JSON + Validation HMAC         │
│  • Publication MQTT                     │
└──────────────┬───────────────────────────┘
               │ MQTT TCP/IP (QoS 1)
               ↓
┌──────────────────────────────────────────┐
│  BROKER MQTT (Mosquitto)                │
│  • Topics: campus/orion/sensors/*       │
│  • Topics: campus/orion/actuators/*     │
└──────────────┬───────────────────────────┘
               │
               ├─→ Backend API (persistance PostgreSQL)
               └─→ Frontend Web (supervision temps réel)
```

## 2.2 Justification des choix techniques

### Microcontrôleurs
| Choix | Justification |
|-------|---------------|
| **Arduino Mega (Gateway)** | 256KB Flash + 4 UART + 8KB RAM → nécessaire pour XBee + HMAC + capteurs |
| **Arduino UNO (End Devices)** | 32KB Flash suffisant pour capteur simple → économie |

### Communication sans fil : ZigBee
| Critère | ZigBee | WiFi | LoRaWAN |
|---------|--------|------|---------|
| **Portée** | 30m indoor | 50m | 2 km |
| **Consommation** | 1 µA idle  80 mA | 1.5 µA |
| **Topologie** | Mesh | Star | Star |
| **Débit** | 250 kbps | 54 Mbps | 0.3 kbps |
| **Coût module** | 30€ | 5€ | 20€ |

**Conclusion** : On a choisi ZigBee car c'est le meilleur compromis pour notre usage en bâtiment (bonne portée, faible consommation et réseau mesh)

### Capteurs
| Capteur | Modèle | Justification |
|---------|--------|---------------|
| **Température/Humidité/Pression** | BME280 | 3-en-1, I2C, 3.6 µA idle, ±0.5°C précision |
| **Présence/Distance** | HC-SR04 | Ultrason 2-400 cm, distance précise vs PIR booléen |
| **CO2** | Potentiomètre (MVP) | Simulation 0-2000 ppm, simple calibration, 0 mA consommation |

### Protocole MQTT
- **QoS 1** : Garantit qu'un message arrive au moins une fois (on accepte d'éventuels doublons)
- **Messages retained** : Le dernier état reste disponible même pour les nouveaux abonnés
- **Topics organisés** : On utilise une structure hiérarchique comme `campus/orion/sensors/{type}` pour faciliter les abonnements

### Sécurité : HMAC-SHA256
- **Authentification** : Permet de vérifier que les messages viennent bien d'un vrai capteur
- **Intégrité** : Détecte si les données ont été modifiées pendant la transmission
- **Coût** : Ajoute 32 bytes par message, ce qui reste acceptable vu notre débit
- **Limite connue** : Pour l'instant le secret est en dur dans le code (à améliorer plus tard avec une rotation des clés)

## 2.3 Schéma électrique Gateway

```
Arduino Mega 2560
├─ I2C (SDA/SCL) → BME280 (0x76)
├─ GPIO 7/8 → HC-SR04 (Trig/Echo)
├─ ADC A0 → Potentiomètre CO2
├─ PWM Pin 5 → Driver L298N → Relay → Moteur 12V
├─ PWM Pin 6 → Transistor NPN → Buzzer
├─ Serial1 (RX/TX) → XBee Coordinator
└─ USB → PC/Raspberry (Serial 9600 baud)

Notes importantes :
- Le XBee est alimenté directement par le shield en 3.3V
- Le moteur nécessite une alimentation externe 12V (l'USB ne suffit pas)
- Le driver L298N sépare bien la partie logique 5V de la partie puissance 12V
```

## 2.4 Limites et performances attendues

### Performances nominales
| Métrique | Valeur |
|----------|--------|
| **Latence capteur → dashboard** | 200-500 ms |
| **Latence commande → actionneur** | 100-300 ms |
| **Capacité réseau ZigBee** | ~50 capteurs @ 60s intervalle |
| **Portée ZigBee indoor** | ~30m (extensible via routeurs) |
| **Autonomie batterie (End Device)** | ~7 jours (sleep mode) |

### Limites identifiées
| Limite | Impact | Mitigation |
|--------|--------|------------|
| **Portée ZigBee 30m** | Bâtiment >50m nécessite routeurs | Ajouter routeurs XBee (~80€/unité) |
| **Alimentation USB** | Capteurs fixes, pas de mobilité | UPS pour continuité secteur |
| **Pas de buffer local** | Données perdues si broker offline | Broker stable Docker + restart auto <1min |
| **Single-node** | Pas de redondance | Backups auto Supabase, alertes email |
| **Secret HMAC hardcodé** | Risque compromission | Rotation clés phase 2 |

---

# 3. DOCUMENTATION UTILISATEUR

## 3.1 Installation du matériel

### Étape 1 : Câblage du Gateway Coordinator
1. **Arduino Mega 2560** + Shield XBee
2. **Capteurs** :
   - BME280 : SDA → Pin 20, SCL → Pin 21, VCC → 3.3V, GND → GND
   - HC-SR04 : Trig → Pin 7, Echo → Pin 8, VCC → 5V, GND → GND
   - Potentiomètre : Signal → A0, VCC → 5V, GND → GND
3. **Actionneurs** :
   - Moteur : PWM Pin 5 → Driver L298N → Relay → Moteur 12V
   - Buzzer : PWM Pin 6 → Transistor NPN → Buzzer piézo
4. **XBee** : Insérer XBee Coordinator sur shield
5. **Alimentation** : USB vers PC + alimentation 12V externe pour moteur

### Étape 2 : Flasher Arduino
```bash
Fichier → Ouvrir → campus-iot/firmware/gateway/gateway.ino
Outils → Carte → Arduino Mega 2560
Outils → Port → /dev/ttyACM0 (Linux) ou COM3 (Windows)
Croquis → Téléverser

# Si tout se passe bien, vous devriez voir dans le Serial Monitor (9600 baud) :
[GATEWAY] BME280 OK
[GATEWAY] HC-SR04 OK
[GATEWAY] Système prêt
```

### Étape 3 : Configurer XBee (XCTU)
**Coordinator (Gateway)** :
```
- Télécharger XCTU : https://www.digi.com/xctu
- Brancher Arduino + XBee au PC
- XCTU → Add Device → Port Arduino
- Charger Firmware : "XBee ZB Coordinator API"
- Configurer :
  * PAN ID : 1234
  * Channel : 15
  * DL : 0x0000 (broadcast)
- Write configuration
```

**End Devices** :
```
- Même procédure
- Charger Firmware : "XBee ZB End Device API"
- PAN ID : 1234 (IDENTIQUE)
- Channel : 15 (IDENTIQUE)
- DL : 0x0000
- Write configuration
- Network Viewer : End Device rejoint réseau (~30 sec)
```

### Étape 4 : Lancer Bridge Python
```bash
cd campus-iot/firmware/gateway
pip install pyserial paho-mqtt
python mqtt_bridge.py

# Output attendu :
[OK] Connecté au port série /dev/ttyACM0 @ 9600 baud
[OK] Connecté au broker MQTT localhost:1883
[BRIDGE] En attente de données série...
```

## 3.2 Utilisation

### Vérifier que les données arrivent bien
```bash
# Terminal 2 : S'abonner aux capteurs
mosquitto_sub -h localhost -p 1883 -t "campus/orion/sensors/#" -v

# Si ça marche, vous verrez défiler les messages :
campus/orion/sensors/temperature {"room":"X101","value":23.5,"ts":...}
campus/orion/sensors/humidity {"room":"X101","value":45.2,"ts":...}
```

### Contrôler actionneurs
```bash
# Via MQTT (terminal 3)
mosquitto_pub -h localhost -p 1883 \
  -t "campus/orion/actuators/motor" \
  -m '{"room":"X101","value":150}'

# Le moteur devrait se mettre à tourner (vitesse 150 sur 255)
```

### Dashboard web (optionnel)
```
URL : http://localhost
- Visualisation temps réel des capteurs
- Contrôle actionneurs via interface
- Historiques et graphiques
```

## 3.3 Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| **Pas de données série** | Arduino pas flashé | Re-flasher gateway.ino, vérifier baud 9600 |
| **XBee ne communique pas** | PAN ID/Channel différent | XCTU : vérifier config identique (1234/15) |
| **Portée insuffisante** | Obstacles béton | Ajouter routeur XBee, placer Coordinator central |
| **MQTT pas connecté** | Mosquitto offline | `docker ps` ou `docker compose up -d` |
| **Moteur ne démarre pas** | Alimentation insuffisante | Vérifier alim externe 12V (pas USB) |
| **HMAC invalide** | Secret différent | Vérifier secret identique End Device/Gateway |

### Checklist déploiement
- [ ] Arduino Mega flashé (gateway.ino)
- [ ] XBee Coordinator configuré (XCTU : PAN 1234, CH 15)
- [ ] XBee End Devices configurés (même PAN/CH)
- [ ] Capteurs câblés (BME280 I2C, HC-SR04 GPIO, Pot A0)
- [ ] Actionneurs câblés (Moteur PWM 5, Buzzer PWM 6)
- [ ] Serial Monitor affiche logs OK
- [ ] Bridge Python lancé et connecté MQTT
- [ ] `mosquitto_sub` reçoit messages capteurs
- [ ] Actionneurs réagissent aux commandes

---

**Support** : https://github.com/Raikuji/IoT_CESI/issues  
**Auteurs** : Groupe 3 FISA INFO - CESI Nancy  
**Date** : 11 février 2026

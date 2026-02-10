# LIVRABLE FINAL - Campus IoT CESI Nancy
## Documentation complète : Architecture, choix techniques et modes d'emploi

**Date** : 10 février 2026  
**Projet** : IoT Campus Intelligent - Bâtiment Orion  
**Établissement** : CESI Nancy  
**Version** : 1.0  
**Dépôt Git** : https://github.com/Raikuji/IoT_CESI

---

## 📋 Table des matières

1. [Architecture complète de la chaîne IoT](#-architecture-complète-de-la-chaîne-iot)
2. [Justification des choix techniques](#-justification-des-choix-techniques)
3. [Limites et performances attendues](#-limites-et-performances-attendues)
4. [Guide utilisateur - Administrateur](#-guide-utilisateur---administrateur)
5. [Guide utilisateur - Usager standard](#-guide-utilisateur---usager-standard)
6. [Guide utilisateur - IoT & Hardware](#-guide-utilisateur---iot--hardware)

---

## 🏗️ Architecture complète de la chaîne IoT

### Schéma global

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPTEURS IOT (Bâtiment Orion)                  │
├─────────────────────────────────────────────────────────────────────┤
│  • BME280 (Température, Humidité, Pression)                         │
│  • HC-SR04 (Distance/Présence)                                      │
│  • Potentiomètre (Luminosité)                                       │
│  • MQ-135 (CO2)                                                     │
│  Connectivité: Serial (I2C, GPIO, ADC) → Arduino Mega              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Liaison série USB (9600 baud)
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│              GATEWAY ARDUINO (Collecteur local)                      │
├─────────────────────────────────────────────────────────────────────┤
│  • Arduino Mega 2560                                                │
│  • XBee Series 2 Coordinator (ZigBee)                               │
│  • Actionneurs: Moteur DC + Speaker                                 │
│  Rôle: Agréger les capteurs locaux, recevoir/envoyer via XBee      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ ZigBee Mesh (250 kbps, ~30m indoor)
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                   CAPTEURS XBEE (End Devices)                       │
├─────────────────────────────────────────────────────────────────────┤
│  • XBee Series 2 (Router/End Device)                                │
│  • Capteurs additionnels (BME280, HC-SR04, etc)                     │
│  Rôle: Capturer et transmettre au Coordinator                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Bridge Python (mqtt_bridge.py)
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    GATEWAY APPLICATION (PC/Server)                  │
├─────────────────────────────────────────────────────────────────────┤
│  • Script Python mqtt_bridge.py                                     │
│  • Lit les données série de l'Arduino                               │
│  • Formate et publie sur MQTT                                       │
│  • Écoute les commandes MQTT pour actionneurs                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                   MQTT over TCP/IP (port 1883)
                   
┌─────────────────────────────────────────────────────────────────────┐
│                       MOSQUITTO BROKER                              │
├─────────────────────────────────────────────────────────────────────┤
│  Port 1883 : MQTT TCP                                               │
│  Port 9001 : MQTT WebSocket (pour frontend)                         │
│  Topics:                                                             │
│    • campus/orion/sensors/{type}     → Données capteurs             │
│    • campus/orion/actuators/{device} → Commandes actionneurs        │
│    • campus/orion/controls/energy/*  → Config énergie               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
    HTTP/REST                              WebSocket
        │                                         │
┌───────▼──────────────────┐    ┌────────────────▼──────────┐
│   BACKEND API (FastAPI)  │    │  FRONTEND (Vue 3)         │
├──────────────────────────┤    ├───────────────────────────┤
│ • Endpoints REST         │    │ • Dashboard temps réel    │
│ • WebSocket connexion    │    │ • Alertes live            │
│ • Client MQTT            │    │ • Admin panel             │
│ • Logique métier         │    │ • Contrôle actionneurs    │
│ • Validation données     │    │ • Export rapports         │
└───────┬──────────────────┘    └───────────────────────────┘
        │
        │ TCP (port 5432)
        │
┌───────▼──────────────────────────────────────┐
│    PostgreSQL Database (Supabase Cloud)      │
├────────────────────────────────────────────────┤
│ • TimescaleDB (time-series)                  │
│ • Tables: sensors, alerts, users, logs...    │
│ • Stockage persistant des mesures            │
└────────────────────────────────────────────────┘
```

### Flux de données

**Scénario 1 : Capteur → Dashboard**

```
1. BME280 mesure température → Arduino Mega
2. Arduino Mega lit via I2C → Serie USB
3. Bridge Python lit série → Parse JSON
4. Bridge publie MQTT "campus/orion/sensors/temperature"
5. Backend s'abonne aux topics MQTT
6. Backend reçoit et enregistre en BDD
7. Frontend connecté en WebSocket reçoit notification
8. Dashboard affiche la donnée en temps réel
```

**Latence totale estimée : < 2 secondes**

**Scénario 2 : Commande actionneur (via API)**

```
1. Admin web clique "Démarrer moteur"
2. Frontend POST /api/actuators/motor/command
3. Backend valide et publie MQTT "campus/orion/actuators/motor"
4. Bridge Python reçoit le message MQTT
5. Bridge envoie commande à Arduino via série
6. Arduino contrôle le relay → Moteur démarre
7. Backend confirme à Frontend (200 OK)
```

**Latence totale estimée : < 1 seconde**

### Justification des choix techniques

#### 1. **Communication capteurs locaux : I2C/GPIO + Arduino Mega**

| Aspect | Choix | Justification |
|--------|-------|---------------|
| **Pourquoi Arduino Mega** | Microcontrôleur robuste + ports multiples | 2x port I2C, PWM, ADC, mémoire suffisante pour HMAC, prix abordable |
| **Pourquoi I2C** | Standard pour capteurs numériques | Consommation faible, 2 fils (SDA/SCL), adressage multiple, fiabilité |
| **Pourquoi GPIO analogique** | Capture du potentiomètre | Conversion ADC 10-bit suffisante (~0.1V précision) |

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

## 📊 Limites et performances attendues

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

#### 3. **Pas de chiffrement MQTT (communication en clair)**

- **Impact** : Quelqu'un sur le réseau local peut écouter les capteurs
- **Raison** : TLS/SSL ajoute latence (~5-10%), réseau interne supposé sécurisé
- **Mitigation** : Réseau WiFi/Ethernet protégé par mot de passe, future évolution avec TLS optionnel

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
| Ajouter TLS sur MQTT | Facile | Sécurité réseau +++ |
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
⚠️ CHANGER le mot de passe initial immédiatement
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

---

## 🛠️ Guide utilisateur - IoT & Hardware

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
│  └─ A0 = Potentiomètre (0-1023)
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
- [ ] Capteurs câblés: BME280 (I2C), HC-SR04 (GPIO 7/8), Potentiomètre (A0)
- [ ] Moteur/Speaker câblés: Relais (PWM 5), Speaker driver (PWM 6)
- [ ] Moniteur série: Messages OK sans erreur
- [ ] Bridge Python lancé: "Connected to MQTT broker"
- [ ] Mosquitto en ligne: `mosquitto_sub` reçoit les messages
- [ ] Backend FastAPI en ligne: `docker ps` montre conteneur "backend"
- [ ] Frontend Vue en ligne: http://localhost accessible
- [ ] Dashboard affiche données temps réel
- [ ] Actionneurs réagissent aux commandes

---

## 📞 Support & Contacts

**Dépôt du projet** :
- GitHub: https://github.com/Raikuji/IoT_CESI
- Cloner: `git clone https://github.com/Raikuji/IoT_CESI.git`
- Issues & PRs: https://github.com/Raikuji/IoT_CESI/issues

**Problèmes logiciels** :
- Frontend: Voir console navigateur (F12)
- Backend: Logs Docker (`docker compose logs backend`)
- Base de données: Dashboard Supabase

**Problèmes hardware** :
- Arduino: XCTU Network Viewer, moniteur série
- XBee: Vérifier XCTU firmware version, PAN ID/Channel
- Capteurs: Tester code Arduino isolé, vérifier alimentation

**Documentation supplémentaire** :
- [README.md](README.md) : Guide d'installation général
- [DOCUMENTATION_IOT.md](DOCUMENTATION_IOT.md) : Guide hardware détaillé
- [architecture_iot.puml](architecture_iot.puml) : Schéma PlantUML
- Swagger API : http://localhost:8000/docs
- XCTU Help : Intégré dans l'application

---

**Version** : 1.0  
**Date** : 10 février 2026  
**Auteurs** : Groupe 3 FISA INFO 2024-2027 (CESI Nancy)  
**Licence** : MIT

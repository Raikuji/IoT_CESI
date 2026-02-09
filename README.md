# Campus IoT - CESI Nancy

> Plateforme IoT de monitoring et gestion intelligente pour le campus CESI Nancy (Bâtiment Orion)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

## 📋 Table des matières

- [À propos](#-à-propos)
- [Architecture](#-architecture)
- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [API Documentation](#-api-documentation)
- [Sécurité](#-sécurité)
- [Auteurs](#-auteurs)

## 🎯 À propos

Campus IoT est une plateforme complète de gestion et de monitoring en temps réel pour les bâtiments intelligents. Développé dans le cadre du projet IoT CESI (FISA INFO 2024-2027), ce système permet de :

- **Surveiller** en temps réel les données de capteurs (température, humidité, CO2, présence, luminosité, pression)
- **Optimiser** la consommation énergétique grâce à des profils intelligents (Normal, Éco, Nuit)
- **Alerter** automatiquement en cas d'anomalies détectées (seuils dépassés, capteurs inactifs)
- **Contrôler** les actionneurs à distance (moteurs, speakers) via interface web ou MQTT
- **Gérer** les utilisateurs avec système de rôles et permissions (Admin, Technicien, Responsable, Utilisateur)

### Contexte
Le bâtiment Orion du campus CESI Nancy est équipé de capteurs IoT communiquant via XBee (ZigBee) avec une gateway Arduino. Les données sont transmises via MQTT vers le backend FastAPI qui les stocke dans une base PostgreSQL (Supabase) et les expose via une interface web Vue.js moderne.

## 🏗️ Architecture

```
┌─────────────────┐
│  Capteurs IoT   │ (Arduino + XBee)
│  - BME280       │ (Température, Humidité, Pression)
│  - HC-SR04      │ (Distance/Présence)
│  - Potentiomètre│ (Luminosité)
│  - MQ-135       │ (CO2)
└────────┬────────┘
         │ ZigBee (XBee)
         ▼
┌─────────────────┐
│   Gateway       │ (Arduino Mega + XBee Coordinator)
│   MQTT Bridge   │ (Python Script)
└────────┬────────┘
         │ MQTT (port 1883)
         ▼
┌─────────────────┐
│  Mosquitto      │ (Broker MQTT)
│  Topics:        │
│  campus/orion/  │
│  sensors/*      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Backend API   │────▶│  PostgreSQL DB  │
│   FastAPI       │     │   (Supabase)    │
│   - REST API    │     │  - TimescaleDB  │
│   - WebSocket   │     │  - Auth JWT     │
│   - MQTT Client │     └─────────────────┘
└────────┬────────┘
         │ HTTP/WS
         ▼
┌─────────────────┐
│   Frontend      │
│   Vue 3 + Vuetify│
│   - Dashboard   │
│   - Alertes     │
│   - Admin       │
└─────────────────┘
```

### Communication MQTT

**Topics principaux :**
- `campus/orion/sensors/{type}` - Publication des données capteurs
- `campus/orion/actuators/{device}` - Commandes actionneurs
- `campus/orion/controls/energy/{sensor_id}` - Configuration énergie

**Format des messages :**
```json
{
  "room": "X101",
  "value": 23.5
}
```

### Justification des choix techniques

| Composant | Choix | Justification |
|-----------|-------|---------------|
| **Communication capteurs** | XBee (ZigBee) | Protocole mesh adapté aux bâtiments : faible consommation, portée ~30m indoor, auto-healing du réseau, jusqu'à 65 000 nœuds |
| **Protocole applicatif** | MQTT | Léger (faible overhead), publish/subscribe idéal pour IoT, QoS configurable, retain pour état persistant, standard industriel |
| **Broker MQTT** | Mosquitto | Open source, léger, stable, supporte WebSocket pour le frontend, configuration simple |
| **Gateway** | Arduino Mega + Python bridge | Arduino gère le hardware (XBee, capteurs), Python assure le pont série→MQTT avec fiabilité |
| **Backend** | FastAPI (Python) | Async natif (WebSocket + MQTT simultanés), auto-documentation Swagger, validation Pydantic, performances élevées |
| **Base de données** | PostgreSQL (Supabase) | Robuste, support time-series via TimescaleDB, hébergement cloud Supabase pour persistance externe |
| **Frontend** | Vue 3 + Vuetify | Réactivité native, écosystème riche (Pinia, Router), composants Material Design prêts à l'emploi |
| **Conteneurisation** | Docker Compose | Déploiement reproductible, isolation des services, scaling facilité |
| **Sécurité capteurs** | HMAC-SHA256 | Authentification des trames XBee sans surcharge de chiffrement complet, adapté aux contraintes mémoire Arduino |
| **Auth web** | JWT + bcrypt | Stateless, scalable, expiration configurable, standard industrie |

### Limites et performances attendues

| Critère | Valeur | Commentaire |
|---------|--------|-------------|
| **Portée XBee indoor** | ~30 m | Réduite par murs béton, extensible via routeurs XBee mesh |
| **Débit XBee** | 250 kbps max | Suffisant pour données capteurs (quelques octets/message) |
| **Latence capteur→dashboard** | < 2 s | XBee (~50ms) + MQTT (~100ms) + WebSocket (~50ms) + render |
| **Nombre capteurs max** | ~65 000 (ZigBee) | En pratique limité par le coordinateur (~20-30 nœuds directs) |
| **Fréquence d'acquisition** | 1-300 s configurable | Mode normal: 60s, éco: 120s, nuit: 300s |
| **Capacité MQTT** | ~10 000 msg/s | Mosquitto sur un seul serveur |
| **Stockage BDD** | ~100 Mo/an | Estimé pour 10 capteurs à 60s d'intervalle |
| **Utilisateurs simultanés** | ~50 | Limité par WebSocket backend (async FastAPI) |
| **Disponibilité** | ~99% (hors maintenance) | Docker restart automatique, pas de HA (single node) |

**Limites identifiées :**
- **Pas de redondance** : Architecture single-node, pas de failover automatique
- **Pas de chiffrement MQTT** : Communication MQTT en clair (pas de TLS), acceptable en réseau local
- **Alimentation capteurs** : Arduino alimenté USB/secteur, pas de batterie (pas de contrainte d'autonomie)
- **Pas de stockage local** : Si le broker/backend tombe, les données capteurs sont perdues (pas de buffer côté gateway)
- **Scalabilité limitée** : Un seul broker MQTT, un seul backend, adapté à un bâtiment (~50 capteurs max)

## ✨ Fonctionnalités

### 🎛️ Dashboard
- **Visualisation temps réel** des capteurs par étage et salle
- **Graphiques d'évolution** (température sur 1h/6h/24h)
- **Indicateurs clés** : Activité capteurs, Mode éco, Température moyenne, Alertes actives
- **Configuration énergie** par capteur (profils Normal/Éco/Nuit, intervalles, planning)

### 🚨 Système d'alertes
- **Détection automatique** des anomalies (seuils, inactivité)
- **Notifications en temps réel** via WebSocket
- **Gestion des alertes** : Acquittement, résolution, historique
- **Escalade automatique** selon la sévérité (info, warning, danger)
- **Filtrage avancé** par type, sévérité, statut

### 🏢 Gestion du bâtiment
- **Hiérarchie** : Floors → Rooms → Sensors
- **Placement dynamique** des capteurs dans les salles
- **Configuration MQTT** pour chaque capteur (topic, intervalle)
- **Types de capteurs** : Temperature, Humidity, CO2, Presence, Pressure, Light

### 🎚️ Contrôle actionneurs
- **Moteur** : Contrôle de vitesse (0-255) avec feedback position
- **Speaker** : Alarmes sonores (température, CO2)
- **API REST** + Interface web pour commandes

### ⚡ Économie d'énergie
- **Profils intelligents** :
  - Normal (100%) : Rafraîchissement 60s
  - Éco (60%) : Rafraîchissement 120s, live désactivé
  - Nuit (40%) : Rafraîchissement 300s, live désactivé
- **Planification automatique** : Jours/heures configurables
- **Estimation** consommation et économies en temps réel
- **Métriques** : Taux d'activité, capteurs en mode éco

### 👥 Administration
- **Gestion utilisateurs** : CRUD complet, activation/désactivation
- **Système de rôles** :
  - **Admin** : Accès total, gestion utilisateurs
  - **Technicien** : Gestion capteurs, alertes, contrôle
  - **Responsable** : Consultation avancée, export données
  - **Utilisateur** : Lecture seule dashboard
- **Statistiques** : Utilisateurs actifs, distribution des rôles
- **Sécurité** : JWT tokens, hashage bcrypt, protection CSRF

### 📊 Journal d'activité
- **Audit trail complet** : Connexions, modifications, actions
- **Filtrage** par utilisateur, type d'action, période
- **Export** des logs en CSV/JSON

### 🔒 Sécurité
- **Authentification HMAC** pour communication XBee
- **JWT** avec expiration configurable
- **Protection injection SQL** (SQLAlchemy ORM)
- **CORS** configuré pour frontend
- **Variables d'environnement** pour secrets

## 🛠️ Technologies

### Backend
- **FastAPI** 0.109 - Framework web Python moderne
- **SQLAlchemy** 2.0 - ORM Python
- **Paho MQTT** - Client MQTT Python
- **PostgreSQL** - Base de données (Supabase)
- **TimescaleDB** - Extension PostgreSQL pour time-series
- **Alembic** - Migration de base de données
- **Pydantic** - Validation de données
- **Python-Jose** - JWT tokens
- **Passlib** - Hashage mots de passe

### Frontend
- **Vue 3** - Framework JavaScript progressif
- **Vuetify 3** - Composants Material Design
- **Pinia** - State management
- **Vue Router** - Routing SPA
- **Axios** - Client HTTP
- **ApexCharts** - Graphiques interactifs
- **Vite** - Build tool moderne

### Infrastructure
- **Docker Compose** - Orchestration conteneurs
- **Nginx** - Reverse proxy (frontend)
- **Mosquitto** - Broker MQTT
- **Git** - Contrôle de version

### Matériel IoT
- **Arduino Mega** - Gateway centrale
- **XBee Series 2** - Communication ZigBee
- **BME280** - Capteur température/humidité/pression
- **HC-SR04** - Capteur ultrason (distance/présence)
- **Potentiomètre** - Simulation luminosité
- **Moteur DC** - Actionneur (ventilation)
- **Speaker** - Actionneur (alarmes)

## 📦 Installation

### Prérequis
- Docker & Docker Compose
- Git
- Python 3.11+ (pour développement)
- Node.js 18+ (pour développement frontend)

### Installation rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/Raikuji/IoT_CESI.git
cd IoT_CESI/campus-iot

# 2. Copier le fichier d'environnement
cp env.example .env

# 3. Configurer les variables d'environnement
nano .env  # Éditer DATABASE_URL, JWT_SECRET, etc.

# 4. Démarrer les conteneurs
docker compose up -d --build

# 5. Initialiser la base de données (première fois)
docker compose exec backend alembic upgrade head

# 6. Créer un utilisateur admin
docker compose exec backend python -c "
from app.db.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

db = SessionLocal()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

admin = User(
    email='admin@cesi.fr',
    password_hash=pwd_context.hash('admin123'),
    first_name='Admin',
    last_name='CESI',
    role='admin',
    department='IT',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin créé : admin@cesi.fr / admin123')
"
```

### Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost | Interface web principale |
| Backend API | http://localhost:8000 | API REST |
| API Docs | http://localhost:8000/docs | Swagger UI (documentation interactive) |
| MQTT Broker | localhost:1883 | Broker Mosquitto |
| MQTT WebSocket | localhost:9001 | MQTT sur WebSocket |

## ⚙️ Configuration

### Variables d'environnement (.env)

```bash
# Database (Supabase)
DATABASE_URL=postgresql://user:password@host:6543/postgres?options=-c%20statement_timeout%3D30000

# JWT Authentication
JWT_SECRET_KEY=votre_secret_super_securise_ici
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=43200  # 30 jours

# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_TOPIC_PREFIX=campus/orion

# CORS (Frontend URL)
FRONTEND_URL=http://localhost

# XBee Security
XBEE_HMAC_KEY=cle_secrete_hmac_xbee
```

### Configuration des capteurs

Les capteurs sont configurés via l'interface web (Dashboard → Clic sur capteur → Économie d'énergie) :

- **Profil** : Normal / Éco / Nuit
- **Intervalle rafraîchissement** : Secondes entre chaque mesure
- **Désactiver temps réel** : Arrête l'envoi continu de données
- **Planning automatique** : Active le profil selon jours/heures

### Configuration MQTT Mosquitto

Fichier `mosquitto/config/mosquitto.conf` :
```conf
listener 1883
protocol mqtt

listener 9001
protocol websockets

allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

## 🚀 Utilisation

### Interface Web

1. **Connexion** : http://localhost avec identifiants admin
2. **Dashboard** : Vue d'ensemble capteurs temps réel
3. **Bâtiment Orion** : Gestion salles et placement capteurs
4. **Alertes** : Consulter et acquitter les alertes actives
5. **Contrôle** : Commander les actionneurs (moteur, speaker)
6. **Administration** : Gérer utilisateurs et rôles (admin uniquement)

### API REST

Documentation complète : http://localhost:8000/docs

**Exemples d'endpoints :**

```bash
# Authentification
POST /api/auth/login
{
  "email": "admin@cesi.fr",
  "password": "admin123"
}

# Récupérer les capteurs
GET /api/building/sensors

# Créer une alerte
POST /api/alerts
{
  "sensor_id": 1,
  "message": "Température élevée",
  "severity": "warning"
}

# Commander un moteur
POST /api/actuators/motor/command
{
  "room_id": "X101",
  "value": 150
}
```

### Communication MQTT

**Publier une mesure de température :**
```bash
mosquitto_pub -h localhost -p 1883 \
  -t "campus/orion/sensors/temperature" \
  -m '{"room": "X101", "value": 23.5}'
```

**S'abonner aux commandes moteur :**
```bash
mosquitto_sub -h localhost -p 1883 \
  -t "campus/orion/actuators/#"
```

### Gateway Arduino

Le script Python `firmware/gateway/mqtt_bridge.py` fait le pont entre XBee et MQTT :

```bash
cd firmware/gateway
pip install -r ../requirements.txt
python mqtt_bridge.py
```

**Commandes interactives :**
- `temp` : Mesure température
- `hum` : Mesure humidité
- `dist` : Mesure distance
- `motor 150` : Contrôle moteur à 150/255
- `pub X108 temp 22` : Publier sur salle spécifique

## 📂 Structure du projet

```
IoT_CESI/
├── campus-iot/                    # Application principale
│   ├── backend/                   # API FastAPI
│   │   ├── app/
│   │   │   ├── api/              # Endpoints REST
│   │   │   │   ├── alerts.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── building.py
│   │   │   │   └── actuators.py
│   │   │   ├── models/           # Modèles SQLAlchemy
│   │   │   ├── schemas/          # Schémas Pydantic
│   │   │   ├── services/         # Logique métier
│   │   │   │   ├── mqtt_client.py
│   │   │   │   └── security_service.py
│   │   │   ├── db/               # Configuration BDD
│   │   │   ├── config.py         # Settings
│   │   │   └── main.py           # Point d'entrée
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── frontend/                  # Application Vue 3
│   │   ├── src/
│   │   │   ├── views/            # Pages
│   │   │   │   ├── DashboardView.vue
│   │   │   │   ├── AlertsView.vue
│   │   │   │   ├── AdminView.vue
│   │   │   │   └── BuildingView.vue
│   │   │   ├── stores/           # Pinia stores
│   │   │   ├── components/       # Composants réutilisables
│   │   │   ├── router/           # Vue Router
│   │   │   └── App.vue
│   │   ├── package.json
│   │   └── Dockerfile
│   ├── mosquitto/                 # Configuration MQTT
│   │   └── config/
│   │       └── mosquitto.conf
│   ├── firmware/                  # Code Arduino/Gateway
│   │   ├── gateway/
│   │   │   ├── gateway.ino       # Code Arduino gateway
│   │   │   └── mqtt_bridge.py    # Script Python XBee→MQTT
│   │   ├── transmitter_bme280/   # Capteur température
│   │   ├── transmitter_ultrasonic/ # Capteur distance
│   │   ├── actuator_motor/       # Actionneur moteur
│   │   └── lib/
│   │       └── hmac_security.h   # Sécurité HMAC
│   ├── docker-compose.yml         # Orchestration Docker
│   └── env.example                # Template variables env
├── configXbee/                    # Configuration XBee
└── README.md                      # Ce fichier
```

## 📚 API Documentation

### Authentification

Toutes les requêtes (sauf `/auth/login` et `/auth/register`) nécessitent un token JWT dans le header :
```
Authorization: Bearer <token>
```

### Endpoints principaux

#### Auth
- `POST /api/auth/login` - Connexion
- `POST /api/auth/register` - Inscription (désactivée en prod)
- `GET /api/auth/me` - Utilisateur actuel

#### Building
- `GET /api/building/floors` - Liste des étages
- `GET /api/building/rooms` - Liste des salles
- `GET /api/building/sensors` - Liste des capteurs placés
- `POST /api/building/sensors` - Placer un capteur
- `DELETE /api/building/sensors/{id}` - Retirer un capteur

#### Alerts
- `GET /api/alerts` - Liste des alertes (filtres : is_resolved, severity)
- `POST /api/alerts` - Créer une alerte
- `PATCH /api/alerts/{id}/ack` - Acquitter une alerte
- `PATCH /api/alerts/{id}/resolve` - Résoudre une alerte

#### Actuators
- `POST /api/actuators/motor/command` - Commander le moteur
- `POST /api/actuators/speaker/command` - Déclencher alarme sonore
- `GET /api/actuators/motor/feedback` - Feedback position moteur

#### Dashboard
- `GET /api/dashboard/stats` - Statistiques agrégées
- `GET /api/activity/logs` - Journal d'activité

#### Admin (Admin uniquement)
- `GET /api/auth/users` - Liste utilisateurs
- `PUT /api/auth/users/{id}` - Modifier utilisateur
- `PATCH /api/auth/users/{id}/role` - Changer rôle
- `DELETE /api/auth/users/{id}` - Supprimer utilisateur

## 🔒 Sécurité

### Implémentées
- ✅ Authentification JWT avec expiration
- ✅ Hashage bcrypt pour mots de passe
- ✅ HMAC pour communication XBee
- ✅ Protection injection SQL (ORM)
- ✅ CORS configuré
- ✅ Variables d'environnement pour secrets
- ✅ Système de rôles et permissions
- ✅ Audit trail des actions utilisateurs
- ✅ Rate limiting sur endpoints sensibles

### Recommandations production
- [ ] HTTPS/TLS pour API et frontend
- [ ] Authentification MQTT (username/password)
- [ ] Chiffrement base de données au repos
- [ ] WAF (Web Application Firewall)
- [ ] Monitoring et alertes sécurité
- [ ] Rotation régulière des secrets
- [ ] Backups automatiques chiffrés

## 👥 Auteurs

**Groupe 3 - FISA INFO 2024-2027**
- Théo PELLIZZARI
- Antoine GACHENOT
- [Autres membres du groupe]

**Établissement :** CESI Nancy  
**Année :** 2025-2026  
**Projet :** IoT Campus Intelligent

## 📄 Licence

Ce projet est développé dans un cadre éducatif pour le CESI.

## 📞 Support

Pour toute question ou problème :
- Email : theo.pellizzari@viacesi.fr
- GitHub Issues : https://github.com/Raikuji/IoT_CESI/issues

---

**Note :** Ce README documente l'état du projet au 9 février 2026. Le projet est fonctionnel et prêt pour démonstration.

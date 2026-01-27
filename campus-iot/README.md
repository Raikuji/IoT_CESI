# Campus IoT - CESI Orion

Système de monitoring IoT pour le campus CESI Nancy - Bâtiment Orion.

## 🚀 Installation rapide

### Prérequis

- **Docker Desktop** (inclut Docker Compose)
  - [Télécharger pour Mac](https://docs.docker.com/desktop/install/mac-install/)
  - [Télécharger pour Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Télécharger pour Linux](https://docs.docker.com/desktop/install/linux-install/)

### Installation en 3 étapes

```bash
# 1. Cloner le projet
git clone https://github.com/Raikuji/IoT_CESI.git
cd IoT_CESI/campus-iot

# 2. Créer le fichier d'environnement
cp env.example .env

# 3. Lancer l'application
docker-compose up -d
```

C'est tout ! L'application est accessible sur **http://localhost**

### Vérifier que tout fonctionne

```bash
# Voir l'état des conteneurs
docker-compose ps

# Tous les conteneurs doivent être "Up" :
# - campus-postgres    (base de données)
# - campus-mosquitto   (broker MQTT)
# - campus-backend     (API)
# - campus-frontend    (interface web)
```

## 🌐 Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| **Application Web** | http://localhost | Interface principale |
| **API Backend** | http://localhost:8000 | API REST |
| **Documentation API** | http://localhost:8000/docs | Swagger UI |
| **MQTT Broker** | localhost:1883 | Pour les capteurs |

## 👤 Connexion

### Compte administrateur par défaut

- **Email** : `theo.pellizzari@viacesi.fr`
- **Mot de passe** : `admin123`

### Créer un nouveau compte

1. Aller sur http://localhost/register
2. Remplir le formulaire d'inscription
3. Se connecter avec les identifiants créés

> **Note** : Les nouveaux comptes ont le rôle "Utilisateur" par défaut. Un admin peut changer les rôles depuis le panel Admin.

## 🔧 Configuration

### Variables d'environnement (.env)

```env
# Base de données
POSTGRES_USER=campus
POSTGRES_PASSWORD=campus_secret
POSTGRES_DB=campus_iot

# Backend
SECRET_KEY=your_super_secret_key_change_me
DATABASE_URL=postgresql://campus:campus_secret@postgres:5432/campus_iot

# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883
```

### Changer le mot de passe admin

1. Se connecter en tant qu'admin
2. Aller dans Profil (icône utilisateur en haut à droite)
3. Section "Changer le mot de passe"

## 📊 Fonctionnalités

### Dashboard
- Vue d'ensemble des capteurs en temps réel
- Filtrage par étage et par salle
- Graphiques d'évolution
- Alertes actives

### Plan du bâtiment
- Vue interactive des étages R+1 et R+2
- Positionnement des capteurs par glisser-déposer
- Visualisation des données par salle

### Gestion des alertes
- Notifications en temps réel (toasts)
- Historique des alertes
- Acquittement des alertes

### Administration
- Gestion des utilisateurs
- Attribution des rôles
- Logs d'activité

### Export de données
- Export CSV/JSON/PDF
- Historique des capteurs
- Rapports

## 🛠️ Commandes utiles

### Gestion Docker

```bash
# Démarrer l'application
docker-compose up -d

# Arrêter l'application
docker-compose down

# Voir les logs en temps réel
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend

# Reconstruire après modification
docker-compose up -d --build

# Tout supprimer (y compris les données)
docker-compose down -v
```

### Réinitialiser la base de données

```bash
# Arrêter et supprimer les volumes
docker-compose down -v

# Relancer (recrée la DB)
docker-compose up -d
```

### Tester l'API

```bash
# Vérifier que l'API répond
curl http://localhost:8000/health

# Obtenir un token (connexion)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=theo.pellizzari@viacesi.fr&password=admin123"
```

### Simuler des données capteurs

```bash
# Publier une température
docker exec campus-mosquitto mosquitto_pub \
  -t "campus/orion/X101/sensors/temperature" -m "23.5"

# Publier une humidité
docker exec campus-mosquitto mosquitto_pub \
  -t "campus/orion/X101/sensors/humidity" -m "45"

# Publier une présence
docker exec campus-mosquitto mosquitto_pub \
  -t "campus/orion/X101/sensors/presence" -m "1"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DOCKER COMPOSE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │PostgreSQL│◄───│ FastAPI  │◄───│  Nginx   │◄─── Navigateur   │
│  │   :5432  │    │  :8000   │    │   :80    │                  │
│  └──────────┘    └────┬─────┘    └──────────┘                  │
│                       │                                         │
│                       │ WebSocket                               │
│                       ▼                                         │
│  ┌──────────┐    ┌──────────┐                                  │
│  │Mosquitto │◄───│ Vue.js   │                                  │
│  │  :1883   │    │ Frontend │                                  │
│  └──────────┘    └──────────┘                                  │
│       ▲                                                         │
│       │ MQTT                                                    │
│       │                                                         │
│  Capteurs (Arduino + XBee + Bridge Python)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Structure du projet

```
campus-iot/
├── backend/                 # API FastAPI (Python)
│   ├── app/
│   │   ├── api/            # Routes API
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── schemas/        # Schémas Pydantic
│   │   ├── services/       # MQTT, WebSocket
│   │   └── main.py         # Point d'entrée
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/               # App Vue.js
│   ├── src/
│   │   ├── views/         # Pages
│   │   ├── components/    # Composants
│   │   ├── stores/        # Pinia stores
│   │   ├── composables/   # Hooks Vue
│   │   └── router/        # Routes
│   ├── Dockerfile
│   └── package.json
│
├── firmware/              # Code Arduino + Bridge
│   ├── gateway/           # Passerelle XBee → MQTT
│   ├── transmitter_*/     # Code capteurs
│   ├── actuator_*/        # Code actionneurs
│   └── README.md          # Doc firmware
│
├── mosquitto/             # Config broker MQTT
├── postgres/              # Init base de données
├── docker-compose.yml     # Orchestration
└── README.md              # Ce fichier
```

## 🔌 Topics MQTT

Format : `campus/orion/{SALLE}/sensors/{TYPE}`

| Topic | Description | Valeurs |
|-------|-------------|---------|
| `.../sensors/temperature` | Température | Float (°C) |
| `.../sensors/humidity` | Humidité | Float (%) |
| `.../sensors/presence` | Présence | 0 ou 1 |
| `.../sensors/light` | Luminosité | 0-100 (%) |
| `.../actuators/motor` | Commande moteur | 0-100, open, close |
| `.../actuators/speaker` | Commande buzzer | beep, warning, danger, co2, stop |

Exemples de salles : `X101`, `X108`, `NUMERILAB`, `FABLAB`, `X201`, etc.

## 🐛 Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
docker-compose logs

# Problème de port déjà utilisé ?
# Modifier les ports dans docker-compose.yml
```

### Erreur de connexion à la base de données

```bash
# Vérifier que postgres est démarré
docker-compose ps postgres

# Voir les logs postgres
docker-compose logs postgres
```

### Les données ne s'affichent pas

1. Vérifier la connexion WebSocket (F12 → Console → "WebSocket connected")
2. Vérifier que le backend est connecté à MQTT (`/health` endpoint)
3. Tester avec une publication MQTT manuelle (voir ci-dessus)

### Réinitialisation complète

```bash
# Tout supprimer et recommencer
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

## 👥 Équipe

Projet A4 FISA - CESI Nancy - Groupe 3

## 📄 Licence

Projet académique - CESI 2026

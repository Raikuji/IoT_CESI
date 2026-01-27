# Campus IoT - CESI Cassiope

Système de monitoring IoT pour le campus CESI Cassiope - Salle C101.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DOCKER COMPOSE                            │
├─────────────────────────────────────────────────────────────────┤
│  Mosquitto (MQTT) ◄─── FastAPI Backend ◄─── PostgreSQL          │
│        ▲                     │                                  │
│        │                     │ WebSocket                        │
│        │                     ▼                                  │
│  Node-RED            Nginx ───► Vue 3 + Vuetify                 │
│                                                                 │
│  Capteurs (XBee) ───► Python Bridge ───► MQTT                   │
└─────────────────────────────────────────────────────────────────┘
```

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Frontend | Vue 3 + Vuetify 3 + Pinia |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + TimescaleDB |
| MQTT Broker | Mosquitto |
| Automations | Node-RED |
| Reverse Proxy | Nginx |
| Conteneurisation | Docker Compose |

## Démarrage rapide

### Prérequis

- Docker & Docker Compose
- Node.js 18+ (pour le dev local)
- Python 3.11+ (pour le dev local)

### Lancement avec Docker

```bash
# Copier le fichier d'environnement
cp env.example .env

# Lancer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

### Accès aux services

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| API Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Node-RED | http://localhost:1880 |
| MQTT | localhost:1883 |

### Credentials par défaut

- **Admin**: `admin` / `admin123`

## Développement local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Topics MQTT

```
campus/cassiope/C101/
├── sensors/
│   ├── temperature      # float (°C)
│   ├── humidity         # float (%)
│   ├── pressure         # float (hPa)
│   ├── presence         # bool (0/1)
│   └── co2              # int (ppm)
├── actuators/
│   ├── heating/status   # int (position servo)
│   └── heating/set      # int (commande)
└── alerts/
    └── #                # alertes système
```

## API Endpoints

### Sensors
- `GET /api/sensors` - Liste des capteurs
- `GET /api/sensors/{id}` - Détail d'un capteur
- `GET /api/sensors/{id}/data` - Historique des données

### Alerts
- `GET /api/alerts` - Liste des alertes
- `POST /api/alerts/{id}/ack` - Acquitter une alerte
- `GET /api/alerts/rules` - Règles d'alerte

### Actuators
- `GET /api/actuators` - Liste des actionneurs
- `POST /api/actuators/{id}/command` - Envoyer une commande

### Dashboard
- `GET /api/dashboard/summary` - Résumé temps réel
- `GET /api/dashboard/stats` - Statistiques agrégées

## Matériel supporté

- **BME280** - Température, humidité, pression
- **HC-SR04** - Détection de présence (ultrason)
- **Servo HS-905BB+** - Contrôle chauffage
- **XBee** - Communication ZigBee

## Équipe

Projet A4 FISA - CESI - Groupe 3

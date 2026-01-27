# Campus IoT - CESI

Système de monitoring IoT pour le campus CESI Nancy.

## Installation rapide


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

L'application est accessible sur **http://localhost**

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

## Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| **Application Web** | http://localhost | Interface principale |
| **API Backend** | http://localhost:8000 | API REST |
| **Documentation API** | http://localhost:8000/docs | Swagger UI |
| **MQTT Broker** | localhost:1883 | Pour les capteurs |

## Connexion

### Créer un nouveau compte

1. Aller sur http://localhost/register
2. Remplir le formulaire d'inscription
3. Se connecter avec les identifiants créés

> **Note** : Les nouveaux comptes ont le rôle "Utilisateur" par défaut. Un admin peut changer les rôles depuis le panel Admin.

## Configuration

### Changer le mot de passe admin

1. Se connecter en tant qu'admin
2. Aller dans Profil (icône utilisateur en haut à droite)
3. Section "Changer le mot de passe"

## Fonctionnalités

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

## Commandes utiles

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

## Topics MQTT

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

## Équipe

Projet A4 FISA - CESI Nancy - Groupe 3

## Licence

Projet académique - CESI 2026

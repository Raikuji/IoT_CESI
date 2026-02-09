Livrable 4 — Campus IoT (Groupe 3 FISA INFO 2024/2027)

Projet : Campus IoT (CESI Nancy – Bâtiment Orion)

Auteurs : BANIZETTE Matthieu, GACHENOT Antoine, PELLIZZARI Théo

Date : 06/02/2026

# 1) Dossier de compréhension et d’analyse

## 1.1 Reformulation du contexte et de ce qui pose question

Le projet Campus IoT instrumente les salles du bâtiment Orion pour collecter des mesures (température, humidité, CO2, présence) et piloter des actionneurs (moteur, speaker). L’architecture repose sur des capteurs et actionneurs reliés à une gateway locale, un broker MQTT Mosquitto et un backend FastAPI (API + WebSocket). Le protocole MQTT est défini (topics, QoS 1, retain, session persistante).

Les composants actifs du projet sont orchestrés par Docker Compose : PostgreSQL (données), Mosquitto (MQTT), backend FastAPI (API), frontend Vue.js servi via Nginx. L’accès principal se fait via http://localhost et l’API est exposée sur http://localhost:8000 avec une documentation Swagger.

La chaîne IoT inclut un firmware (Arduino + XBee) et un bridge gateway vers MQTT, ainsi que des codes dédiés aux capteurs et actionneurs. Les topics MQTT suivent le format campus/orion/{SALLE}/sensors/{TYPE} et campus/orion/{SALLE}/actuators/{TYPE}.

Les questions clés portent sur la fiabilité des données, la sécurité des échanges et la sobriété énergétique :

- Comment garantir l’intégrité et l’authenticité des mesures et commandes ?
- Comment limiter les pertes de messages lors des micro‑coupures réseau ?
- Comment réduire le trafic tout en conservant la réactivité en cas d’anomalie ?
- Comment tracer les actions et les événements critiques de manière robuste ?

Ces points exigent une architecture durable et sécurisée, cohérente avec les contraintes IoT et les recommandations ETSI EN 303 645.



<div style="page-break-before: always;"></div>

## 1.2 Enjeux techniques, énergétiques et de confiance

### Enjeux techniques

- Fiabilité de transport : garantir la livraison des messages sensibles via QoS 1 et sessions persistantes.
- Interopérabilité : topics normalisés et payloads cohérents.
- Scalabilité : capacité à ajouter des salles et des capteurs sans refonte.
- Observabilité : logs et métriques pour diagnostiquer latence, pertes et charge.
- Temps réel : flux WebSocket vers le frontend pour l’affichage des mesures et des alertes.
- Cohérence des données : création automatique des capteurs à la réception MQTT et placement associé dans les plans.
- Détection : règles d’alertes et anomalies disponibles côté backend.

### Enjeux énergétiques

- Sobriété réseau : limiter la fréquence d’émission et adapter les rythmes selon l’état (nominal/alerte).
- Sobriété côté capteurs : éviter les envois inutiles avec des deltas et des heartbeats.
- Rythmes définis par type de capteur : BME280, présence, potentiomètre, afin de réduire le trafic en régime stable.

### Enjeux de confiance

- Authentification des utilisateurs avec JWT et rôles, comme prévu dans le backend.
- Intégrité des données avec HMAC‑SHA256 et vérification d’horodatage.
- Traçabilité applicative via journaux d’audit et historiques d’alertes.
- Traçabilité système : logs Mosquitto et logs applicatifs FastAPI.
- Gestion des comptes : création, rôles et panel d’administration.

<div style="page-break-before: always;"></div>

## 1.3 Vision globale des éléments à fiabiliser, sécuriser ou améliorer

1. Fiabilisation des échanges MQTT
   - Maintenir QoS 1, retain pour les mesures critiques, sessions persistantes.
   - Clarifier les topics et les formats de payload utilisés.
   - Utiliser les topics officiels capteurs/actuateurs déjà définis dans le projet.

2. Sécurisation applicative
   - Appliquer l’authentification JWT et les rôles sur les accès du backend.
   - Vérifier systématiquement l’intégrité HMAC côté backend.
   - Limiter les actions d’administration via le panel et l’API.

3. Intégrité et validation
   - Normaliser les unités et contrôler les valeurs aberrantes.
   - Valider les timestamps pour éviter les messages obsolètes.
   - Rejeter les messages mal formés ou incomplets côté backend.

4. Traçabilité
   - Conserver un historique des alertes, actions et connexions dans la base.
   - S’appuyer sur l’API d’audit déjà présente côté backend.
   - Conserver les exports et les sauvegardes pour la preuve et l’analyse.

5. Sobriété énergétique
   - Conserver des rythmes d’émission adaptés (ex. BME280 60 s ou 30 s en alerte, présence avec heartbeat, potentiomètre sur delta).
   - Limiter les publications aux changements significatifs.

<div style="page-break-before: always;"></div>

# 2) Proposition d’architecture IoT sécurisée et durable

## 2.1 Architecture IoT fonctionnelle (objets, communications, services)

### Objets IoT

- Capteurs : BME280 (temp/hum), capteur CO2, capteur de présence (HC‑SR04), potentiomètre.
- Actuateurs : moteur (ouverture/fermeture), speaker (alertes).
- Topics capteurs : température, humidité, présence, luminosité.
- Topics actionneurs : motor et speaker, avec commandes standardisées.

### Gateway locale

- Agrégation des capteurs et publication vers le broker MQTT.
- Pré‑traitement léger (deltas) et signature HMAC des messages.
- Bridge MQTT depuis la gateway pour les capteurs Arduino/XBee.

### Broker MQTT (Mosquitto)

- Topics structurés : campus/orion/{ROOM}/...
- QoS 1, retain sur capteurs, sessions persistantes.
- Persistance activée et logs Mosquitto disponibles.
- Double listener : MQTT sur 1883 et WebSocket sur 9001.

### Backend (FastAPI)

- Validation HMAC et timestamp.
- Gestion des alertes et des anomalies.
- APIs REST et WebSocket pour le front.
- Documentation Swagger disponible sur /docs.
- Services internes pour exports, backups, webhooks, rapports et intégrations.

<div style="page-break-before: always;"></div>

### Frontend

- Supervision via tableaux de bord, alertes et historiques.
- Plan du bâtiment avec placement des capteurs.
- Gestion des utilisateurs et rôles via panneau d’administration.

### Base de données

- Stockage des mesures, alertes et journaux d’audit.
- Historique des capteurs, anomalies et règles d’alerte.

## 2.2 Intégration des mécanismes de sécurité IoT

### Authentification

- Utilisateurs via JWT et rôles (admin/technician/manager/user) comme défini dans le backend.
- Séparation des accès lecture/administration via les rôles applicatifs.
- Authentification via l’API et gestion des tokens côté frontend.

### Intégrité

- HMAC‑SHA256 sur les messages capteurs et commandes.
- Vérification des timestamps côté backend.
- Rejet des messages sans signature ou avec horodatage incohérent.
- Vérification côté backend avant insertion en base.

### Autorisation

- Accès applicatif contrôlé par rôles pour les actions sensibles.
- Journalisation des actions d’administration via l’API d’audit.
- Accès restreint aux fonctions d’export et de backup.

<div style="page-break-before: always;"></div>

## 2.3 Traçabilité

La traçabilité repose sur les journaux applicatifs du backend et l’historisation des événements (alertes, commandes, connexions). Les exports et sauvegardes permettent de conserver des preuves et de faciliter l’audit.

Les exports s’appuient sur les mécanismes déjà présents dans le projet (dossiers exports et backups) pour conserver des traces exploitables en cas d’incident ou de demande d’audit. Les logs Mosquitto complètent la traçabilité des flux MQTT.

# 3) Restitution synthétique et argumentée

## 3.1 Choix réalisés

- MQTT QoS 1, retain et sessions persistantes.
- Rythmes d’émission adaptés aux capteurs.
- Intégrité HMAC‑SHA256 et validation des timestamps.
- Authentification JWT avec rôles.
- Journalisation et audit côté backend.
- Supervision en temps réel via WebSocket.

## 3.2 Bénéfices attendus

- Meilleure fiabilité des mesures et commandes malgré les micro‑coupures.
- Trafic réduit en régime normal, réactivité conservée en alerte.
- Confiance renforcée via l’authentification et l’intégrité.
- Audit simplifié grâce aux historiques et journaux.
- Vision temps réel du bâtiment et des salles.
- Détection des anomalies et alertes centralisées.

## 3.3 Limites et risques

- Complexité de maintenance des clés HMAC et des comptes.
- Risque de dérive si les règles d’émission ne sont pas respectées.
- Dépendance à la qualité du réseau local.
- Sécurité MQTT limitée si l’accès est ouvert sans authentification côté broker.
- Charge accrue si le rythme d’émission n’est pas respecté.

<div style="page-break-before: always;"></div>

## 3.4 Cohérence globale

La proposition s’appuie sur les choix validés au Livrable 3 (MQTT, QoS 1, retain, sessions persistantes) et les mécanismes applicatifs existants (JWT, HMAC, audit). L’ensemble reste cohérent avec un déploiement Edge sur un campus.

Les éléments décrits sont alignés avec les composants déjà présents (Mosquitto, backend FastAPI, logs/audit, exports/backup) et ne nécessitent pas d’ajout de technologies externes.

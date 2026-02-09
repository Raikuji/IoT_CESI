# Plan de test Sécurité (HMAC + Blockchain)

Date : 09/02/2026

## Objectif
Valider que la page Sécurité et l’API détectent correctement :
- des signatures HMAC valides / invalides,
- des timestamps expirés,
- l’intégrité de la blockchain,
- la génération d’alertes de sécurité.

## Pré-requis
- Backend + base + broker démarrés via docker-compose.
- Frontend accessible sur http://localhost.

## Format de payload attendu
TYPE:VALUE|ts:TIMESTAMP|sig:SIGNATURE
Exemple : temperature:23.5|ts:1700000000000|sig:...

## Scénarios HMAC (UI page Sécurité)
1) Signature valide (générée par l’API)
- Action : cliquer « Générer un payload » puis « Vérifier ».
- Attendu : message « Signature valide » + result.message = valid.

2) Signature valide (message manuel)
- Action : saisir un message simple (ex. temperature:23.5), cliquer « Signer », puis « Vérifier ».
- Attendu : validation OK.

3) Signature invalide (payload modifié)
- Action : générer un payload puis modifier une valeur (ex. 23.5 → 99.9) sans changer la signature, puis « Vérifier ».
- Attendu : validation KO + message « Invalid signature » + création d’une alerte.

4) Timestamp expiré
- Action : générer un payload puis remplacer le timestamp par une valeur très ancienne, puis « Vérifier ».
- Attendu : validation KO + message « Timestamp expired » + création d’une alerte.

5) Payload sans signature
- Action : saisir uniquement TYPE:VALUE|ts:TIMESTAMP puis « Vérifier ».
- Attendu : statut « unsigned » (compatibilité héritée) sans alerte.

## Scénarios Blockchain (UI page Sécurité)
6) Chaîne valide
- Action : cliquer « Vérifier » dans la section Blockchain.
- Attendu : chaîne « Valide ».

7) Bloc ajouté manuellement
- Action : ajouter un bloc via l’API de test (endpoint add) puis recharger.
- Attendu : nouveau bloc visible, signature_valid = true.

8) Chaîne corrompue (test DB)
- Action : modifier un bloc en base (hash ou previous_hash).
- Attendu : « Chaîne » = Erreur, /blockchain/verify renvoie invalid.

## Scénarios MQTT (flux réel capteur)
9) Publication valide
- Action : publier un payload signé sur un topic capteur valide.
- Attendu : mesure enregistrée + bloc ajouté + signature_valid = true.

10) Publication invalide
- Action : publier un payload signé avec une signature incorrecte.
- Attendu : alerte de sécurité + pas d’insertion de données fiables.

## Points de contrôle
- Statistiques dans la page Sécurité : total blocs, signatures OK/KO, alertes.
- Alertes listées et résolvables.
- Chaîne vérifiable et cohérente.

## Fichiers utiles
- UI : [frontend/src/views/SecurityView.vue](../frontend/src/views/SecurityView.vue)
- API : [backend/app/api/security.py](../backend/app/api/security.py)
- Logique HMAC/Blockchain : [backend/app/services/security_service.py](../backend/app/services/security_service.py)

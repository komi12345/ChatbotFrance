# Document des Exigences - Migration WhatsApp Meta Cloud API vers Gupshup 2025

## Introduction

Ce document définit les exigences pour la migration complète de l'intégration WhatsApp du système de chatbot existant. Le système actuel utilise WhatsApp Business API (Meta Cloud API directement) et doit être migré vers Gupshup API (version 2025) tout en conservant exactement les mêmes fonctionnalités et la même architecture globale.

L'objectif est de remplacer uniquement la couche d'intégration WhatsApp sans modifier le frontend Next.js, la structure de la base de données Supabase, ni la logique métier existante.

### Architecture Cible

```
Dashboard Admin (Next.js 14+)
         ↕
API REST Backend Python (FastAPI)
         ↕
Gupshup API (2025) ← NOUVELLE INTÉGRATION
         ↕
WhatsApp Business Platform
         ↕
Base de données Supabase (PostgreSQL)
```

### Informations Gupshup (2025)

- **Application Name** : newsteck
- **WhatsApp Phone Number** : 33753117215 (+33 7 53 11 72 15)
- **Customer ID** : 4000322028
- **API Endpoint** : https://api.gupshup.io/sm/api/v1
- **Status** : Live (Actif)
- **Tier** : BM Level (250 Customers/24 Hrs)

## Glossaire

- **Système** : L'ensemble de l'application comprenant le dashboard frontend et le backend API
- **Backend** : Le serveur API REST FastAPI
- **Gupshup** : Plateforme de messagerie cloud fournissant l'accès à WhatsApp Business API
- **Meta Cloud API** : L'ancienne API WhatsApp Business de Meta (à remplacer)
- **Message 1** : Le message initial envoyé via un template WhatsApp approuvé
- **Message 2** : Le message de suivi automatique envoyé après interaction
- **Template** : Un modèle de message pré-approuvé sur Gupshup Dashboard
- **Webhook** : Un endpoint HTTP recevant les notifications de Gupshup
- **Rate Limiting** : Limitation du nombre de requêtes par unité de temps (250 msg/24h, ~25 msg/min)
- **x-www-form-urlencoded** : Format de données utilisé par Gupshup API (différent du JSON de Meta)
- **apikey** : Clé d'authentification Gupshup (remplace le Bearer token de Meta)
- **src.name** : Nom de l'application source dans les requêtes Gupshup
- **message-event** : Type de webhook Gupshup pour les statuts de livraison

## Exigences

### Exigence 1 : Configuration Gupshup

**User Story:** En tant que développeur, je veux configurer les nouvelles variables d'environnement Gupshup, afin de permettre la connexion à l'API Gupshup 2025.

#### Critères d'Acceptation

1. WHEN le Backend démarre THEN le Système SHALL charger les variables GUPSHUP_API_KEY, GUPSHUP_APP_NAME, GUPSHUP_PHONE_NUMBER depuis le fichier .env
2. WHEN une variable Gupshup obligatoire est manquante THEN le Backend SHALL afficher une erreur explicite au démarrage
3. WHEN les anciennes variables Meta sont présentes THEN le Système SHALL les ignorer sans erreur
4. WHEN la configuration est chargée THEN le Système SHALL définir l'URL de base comme https://api.gupshup.io/sm/api/v1
5. WHEN le fichier .env.example est consulté THEN le Système SHALL documenter toutes les nouvelles variables Gupshup

### Exigence 2 : Service Gupshup - Envoi de Templates

**User Story:** En tant que système, je veux envoyer des messages templates via Gupshup API, afin de délivrer le Message 1 aux contacts.

#### Critères d'Acceptation

1. WHEN un template est envoyé THEN le Backend SHALL utiliser l'endpoint POST https://api.gupshup.io/sm/api/v1/template/msg
2. WHEN une requête template est construite THEN le Backend SHALL utiliser le format x-www-form-urlencoded avec les champs channel, source, destination, template, src.name
3. WHEN le numéro de téléphone est formaté THEN le Backend SHALL retirer le caractère "+" pour obtenir le format Gupshup (ex: 33612345678)
4. WHEN les paramètres du template sont fournis THEN le Backend SHALL les encoder en JSON dans le champ template avec le format {"id": "template_name", "params": ["param1", "param2"]}
5. WHEN l'API Gupshup retourne status "success" THEN le Backend SHALL extraire le messageId et retourner un succès
6. WHEN l'API Gupshup retourne status "error" THEN le Backend SHALL logger l'erreur et retourner un échec avec les détails

### Exigence 3 : Service Gupshup - Envoi de Messages Texte

**User Story:** En tant que système, je veux envoyer des messages texte libre via Gupshup API, afin de délivrer le Message 2 automatique aux contacts.

#### Critères d'Acceptation

1. WHEN un message texte est envoyé THEN le Backend SHALL utiliser l'endpoint POST https://api.gupshup.io/sm/api/v1/msg
2. WHEN une requête message est construite THEN le Backend SHALL utiliser le format x-www-form-urlencoded avec les champs channel, source, destination, message, src.name
3. WHEN le header apikey est défini THEN le Backend SHALL utiliser la clé GUPSHUP_API_KEY
4. WHEN le message contient des caractères spéciaux THEN le Backend SHALL encoder correctement le contenu
5. WHEN l'API Gupshup retourne status "success" THEN le Backend SHALL extraire le messageId et mettre à jour le statut du message
6. WHEN l'API Gupshup retourne status "error" THEN le Backend SHALL programmer un retry selon la logique existante

### Exigence 4 : Webhooks Gupshup - Réception des Messages

**User Story:** En tant que système, je veux recevoir et traiter les webhooks Gupshup pour les messages entrants, afin de déclencher l'automatisation du Message 2.

#### Critères d'Acceptation

1. WHEN un webhook Gupshup de type "message" est reçu THEN le Backend SHALL extraire le numéro mobile, le texte et le messageId
2. WHEN le numéro mobile est extrait THEN le Backend SHALL rechercher le contact correspondant dans la base de données
3. WHEN un contact est trouvé avec un Message 1 récent THEN le Backend SHALL vérifier si le Message 2 doit être envoyé
4. WHEN le Message 2 doit être envoyé THEN le Backend SHALL créer une tâche Celery pour l'envoi automatique
5. WHEN l'interaction est traitée THEN le Backend SHALL enregistrer l'interaction dans la table interactions
6. WHEN le webhook est traité THEN le Backend SHALL retourner un statut 200 OK dans les 20 secondes

### Exigence 5 : Webhooks Gupshup - Statuts de Livraison

**User Story:** En tant que système, je veux recevoir et traiter les webhooks Gupshup pour les statuts de livraison, afin de mettre à jour le tracking des messages.

#### Critères d'Acceptation

1. WHEN un webhook Gupshup de type "message-event" est reçu THEN le Backend SHALL extraire le eventType (sent, delivered, read, failed)
2. WHEN le eventType est "delivered" THEN le Backend SHALL mettre à jour le statut du message à "delivered" avec l'horodatage
3. WHEN le eventType est "read" THEN le Backend SHALL mettre à jour le statut du message à "read" avec l'horodatage
4. WHEN le eventType est "failed" THEN le Backend SHALL marquer le message comme échoué et logger la raison
5. WHEN le externalId est présent THEN le Backend SHALL l'utiliser pour identifier le message dans la base de données
6. WHEN le statut est mis à jour THEN le Backend SHALL incrémenter les compteurs de la campagne correspondante

### Exigence 6 : Adaptation des Tâches Celery

**User Story:** En tant que système, je veux que les tâches Celery utilisent le nouveau service Gupshup, afin de maintenir l'envoi massif asynchrone.

#### Critères d'Acceptation

1. WHEN une tâche d'envoi de campagne est exécutée THEN le Système SHALL utiliser gupshup_service au lieu de whatsapp_service
2. WHEN les messages sont envoyés en lot THEN le Système SHALL respecter la limite de 25 messages par minute
3. WHEN un message échoue THEN le Système SHALL programmer un retry avec délai exponentiel (60s, 120s, 240s)
4. WHEN le retry atteint 3 tentatives THEN le Système SHALL marquer le message comme définitivement échoué
5. WHEN un message réussit THEN le Système SHALL stocker le gupshup_message_id dans la table messages
6. WHEN la campagne est terminée THEN le Système SHALL mettre à jour les statistiques de la campagne

### Exigence 7 : Adaptation des Routes Campagnes

**User Story:** En tant que système, je veux que les routes de campagnes utilisent le nouveau service Gupshup, afin de maintenir la fonctionnalité d'envoi.

#### Critères d'Acceptation

1. WHEN une campagne est lancée THEN le Backend SHALL utiliser gupshup_service pour l'envoi des templates
2. WHEN les contacts sont récupérés THEN le Backend SHALL formater les numéros au format Gupshup (sans +)
3. WHEN le template est spécifié THEN le Backend SHALL utiliser le nom du template approuvé sur Gupshup Dashboard
4. WHEN l'envoi est déclenché THEN le Backend SHALL créer une tâche Celery avec les paramètres Gupshup
5. WHEN les statistiques sont calculées THEN le Backend SHALL utiliser les mêmes formules qu'avant la migration

### Exigence 8 : Rétrocompatibilité et Nettoyage

**User Story:** En tant que développeur, je veux que la migration soit propre et rétrocompatible, afin de faciliter la maintenance future.

#### Critères d'Acceptation

1. WHEN le service whatsapp_service.py est remplacé THEN le Système SHALL créer gupshup_service.py avec la même interface publique
2. WHEN les imports sont mis à jour THEN le Système SHALL remplacer whatsapp_service par gupshup_service dans tous les fichiers
3. WHEN le modèle Message est utilisé THEN le Système SHALL stocker l'ID Gupshup dans le champ whatsapp_message_id existant
4. WHEN la base de données est consultée THEN le Système SHALL fonctionner sans modification du schéma
5. WHEN le frontend appelle l'API THEN le Système SHALL retourner les mêmes formats de réponse qu'avant

### Exigence 9 : Documentation de Migration

**User Story:** En tant que développeur, je veux une documentation complète de la migration, afin de comprendre les changements et configurer le système.

#### Critères d'Acceptation

1. WHEN la documentation est consultée THEN le Système SHALL fournir un guide de migration dans docs/MIGRATION-GUPSHUP.md
2. WHEN les différences API sont expliquées THEN le Système SHALL comparer les formats Meta vs Gupshup
3. WHEN la configuration webhook est décrite THEN le Système SHALL fournir l'URL à configurer sur Gupshup Dashboard
4. WHEN les templates sont mentionnés THEN le Système SHALL expliquer comment les créer sur Gupshup
5. WHEN le troubleshooting est nécessaire THEN le Système SHALL lister les erreurs communes et leurs solutions

### Exigence 10 : Tests d'Intégration Gupshup

**User Story:** En tant que développeur, je veux des tests d'intégration pour valider la migration, afin de garantir le bon fonctionnement du système.

#### Critères d'Acceptation

1. WHEN un test d'envoi de template est exécuté THEN le Système SHALL valider le format de la requête Gupshup
2. WHEN un test d'envoi de message texte est exécuté THEN le Système SHALL valider l'encodage x-www-form-urlencoded
3. WHEN un test de webhook message est exécuté THEN le Système SHALL valider le parsing du payload Gupshup
4. WHEN un test de webhook message-event est exécuté THEN le Système SHALL valider la mise à jour des statuts
5. WHEN un test de formatage de numéro est exécuté THEN le Système SHALL valider la suppression du caractère "+"

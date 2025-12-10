# Requirements Document

## Introduction

Ce document définit les exigences pour la migration du système de chatbot WhatsApp actuellement intégré avec **Twilio Sandbox** vers **Wassenger 2025**. La migration vise à remplacer complètement l'intégration Twilio par Wassenger tout en conservant le workflow existant : envoi de Message 1, réception d'interactions via webhook, envoi automatique de Message 2, et affichage des statistiques en temps réel.

Wassenger est une plateforme d'API WhatsApp qui permet d'envoyer des messages via WhatsApp Business App (connexion QR code) ou WhatsApp Business API. Cette migration permettra également de configurer un profil business professionnel pour masquer le numéro de téléphone et afficher un nom de chatbot personnalisé.

## Glossaire

- **Wassenger** : Plateforme d'API WhatsApp permettant l'envoi et la réception de messages via REST API
- **API Key Wassenger** : Token d'authentification pour l'API Wassenger (format: `wsp_live_...`)
- **Device ID** : Identifiant unique de l'appareil WhatsApp connecté à Wassenger
- **Webhook** : Endpoint HTTP recevant les notifications d'événements de Wassenger
- **Message 1** : Premier message envoyé lors d'une campagne (peut être un template ou texte libre)
- **Message 2** : Message de suivi automatique envoyé après interaction du contact
- **Interaction** : Réponse ou réaction d'un contact à un message reçu
- **Profil Business WhatsApp** : Configuration du compte WhatsApp Business incluant nom, photo, description
- **Fenêtre 24h** : Période pendant laquelle des messages libres peuvent être envoyés après une interaction client

## Requirements

### Requirement 1: Configuration et Authentification Wassenger

**User Story:** En tant qu'administrateur système, je veux configurer les credentials Wassenger dans l'application, afin de pouvoir envoyer des messages WhatsApp via la nouvelle API.

#### Acceptance Criteria

1. WHEN l'application démarre THEN le système SHALL charger les variables d'environnement WASSENGER_API_KEY et WASSENGER_DEVICE_ID depuis le fichier .env
2. WHEN une variable d'environnement Wassenger obligatoire est manquante THEN le système SHALL afficher un message d'erreur explicite indiquant la variable manquante
3. WHEN le service Wassenger est initialisé THEN le système SHALL configurer le client HTTP avec le header Authorization Bearer contenant l'API Key
4. WHEN une requête API est envoyée THEN le système SHALL inclure le Device ID dans le corps de la requête ou l'URL selon l'endpoint

### Requirement 2: Service d'Envoi de Messages Wassenger

**User Story:** En tant que système backend, je veux envoyer des messages WhatsApp via l'API Wassenger, afin de remplacer l'intégration Twilio existante.

#### Acceptance Criteria

1. WHEN un message texte est envoyé THEN le système SHALL appeler l'endpoint POST https://api.wassenger.com/v1/messages avec le payload contenant phone, message et device
2. WHEN un numéro de téléphone est fourni THEN le système SHALL le formater sans le préfixe "+" (format: 22890123456)
3. WHEN l'API Wassenger retourne un succès THEN le système SHALL extraire le message_id de la réponse et le stocker dans whatsapp_message_id
4. WHEN l'API Wassenger retourne une erreur THEN le système SHALL parser le code d'erreur et le message, puis les stocker dans error_message
5. WHEN un message est envoyé THEN le système SHALL respecter un délai minimum de 2 secondes entre chaque envoi pour éviter le rate limiting
6. WHEN une erreur réseau survient THEN le système SHALL réessayer jusqu'à 3 fois avec un délai exponentiel (60s, 120s, 240s)

### Requirement 3: Réception et Parsing des Webhooks Wassenger

**User Story:** En tant que système backend, je veux recevoir et traiter les webhooks Wassenger, afin de détecter les interactions des contacts et mettre à jour les statuts de livraison.

#### Acceptance Criteria

1. WHEN un webhook Wassenger est reçu sur l'endpoint /api/webhooks/wassenger THEN le système SHALL parser le payload JSON selon le format Wassenger 2025
2. WHEN l'événement est "message:in:new" THEN le système SHALL extraire le numéro de téléphone de l'expéditeur (data.fromNumber), le contenu du message (data.body) et l'ID du message (data.id)
3. WHEN l'événement est "message:out:sent" THEN le système SHALL mettre à jour le statut du message correspondant à "sent"
4. WHEN l'événement est "message:out:delivered" THEN le système SHALL mettre à jour le statut du message correspondant à "delivered" avec horodatage
5. WHEN l'événement est "message:out:read" THEN le système SHALL mettre à jour le statut du message correspondant à "read" avec horodatage
6. WHEN l'événement est "message:out:failed" THEN le système SHALL mettre à jour le statut du message correspondant à "failed" avec le message d'erreur
7. WHEN un webhook est traité avec succès THEN le système SHALL retourner un statut HTTP 200 OK immédiatement

### Requirement 4: Automatisation Message 2 après Interaction

**User Story:** En tant qu'administrateur de campagne, je veux que le Message 2 soit envoyé automatiquement après qu'un contact répond, afin de maintenir l'engagement sans intervention manuelle.

#### Acceptance Criteria

1. WHEN un message entrant est reçu (événement message:in:new) THEN le système SHALL rechercher le contact par son numéro de téléphone dans la base de données
2. WHEN le contact est trouvé THEN le système SHALL vérifier s'il a reçu un Message 1 dans les dernières 24 heures
3. WHEN un Message 1 récent existe THEN le système SHALL vérifier si un Message 2 a déjà été envoyé pour cette campagne
4. WHEN aucun Message 2 n'a été envoyé THEN le système SHALL créer un enregistrement Message 2 et programmer son envoi via Celery
5. WHEN un Message 2 a déjà été envoyé THEN le système SHALL ignorer l'interaction sans envoyer de nouveau message
6. WHEN l'interaction est enregistrée THEN le système SHALL incrémenter le compteur d'interactions de la campagne

### Requirement 5: Migration des Variables d'Environnement

**User Story:** En tant que développeur, je veux que les variables d'environnement Twilio soient remplacées par celles de Wassenger, afin de configurer correctement la nouvelle intégration.

#### Acceptance Criteria

1. WHEN le fichier .env est configuré THEN le système SHALL reconnaître les variables WASSENGER_API_KEY, WASSENGER_DEVICE_ID et WASSENGER_WEBHOOK_URL
2. WHEN les anciennes variables TWILIO_* sont présentes THEN le système SHALL les ignorer sans générer d'erreur
3. WHEN le fichier .env.example est mis à jour THEN le système SHALL documenter chaque variable Wassenger avec des commentaires explicatifs en français
4. WHEN la configuration est validée au démarrage THEN le système SHALL vérifier que WASSENGER_API_KEY et WASSENGER_DEVICE_ID sont non vides

### Requirement 6: Mise à Jour du Service de Messages

**User Story:** En tant que système backend, je veux que le service de messages utilise Wassenger au lieu de Twilio, afin que toutes les fonctionnalités existantes continuent de fonctionner.

#### Acceptance Criteria

1. WHEN une campagne est lancée THEN le système SHALL utiliser wassenger_service.send_message() au lieu de twilio_service.send_message()
2. WHEN un Message 2 est déclenché THEN le système SHALL utiliser wassenger_service pour l'envoi
3. WHEN les statistiques sont calculées THEN le système SHALL utiliser les mêmes champs de base de données (whatsapp_message_id, status, sent_at, delivered_at, read_at)
4. WHEN un retry est programmé THEN le système SHALL utiliser wassenger_service avec le même délai exponentiel

### Requirement 7: Gestion des Erreurs Spécifiques Wassenger

**User Story:** En tant qu'administrateur, je veux comprendre les erreurs d'envoi Wassenger, afin de pouvoir diagnostiquer et résoudre les problèmes.

#### Acceptance Criteria

1. WHEN l'erreur "device_not_connected" est retournée THEN le système SHALL afficher un message indiquant que l'appareil WhatsApp doit être reconnecté via QR code
2. WHEN l'erreur "invalid_phone_number" est retournée THEN le système SHALL afficher un message indiquant que le format du numéro est incorrect
3. WHEN l'erreur "rate_limit_exceeded" est retournée THEN le système SHALL attendre 60 secondes avant de réessayer
4. WHEN l'erreur "session_expired" est retournée THEN le système SHALL afficher un message indiquant que la session WhatsApp a expiré
5. WHEN une erreur inconnue est retournée THEN le système SHALL logger le code et le message d'erreur complets pour diagnostic

### Requirement 8: Documentation de Migration

**User Story:** En tant que développeur, je veux une documentation complète de la migration, afin de pouvoir configurer et lancer le projet avec Wassenger.

#### Acceptance Criteria

1. WHEN le guide GUIDE_LANCEMENT_PROJET_WASSENGER_2025.md est créé THEN le document SHALL contenir les sections prérequis, configuration Supabase, configuration backend, configuration frontend, lancement local, configuration ngrok, configuration webhook Wassenger, tests du workflow et dépannage
2. WHEN le guide GUIDE_CONFIGURATION_WASSENGER_2025.md est créé THEN le document SHALL contenir les étapes détaillées pour créer un compte Wassenger, connecter WhatsApp, obtenir l'API Key, obtenir le Device ID et configurer les webhooks
3. WHEN le guide GUIDE_CONFIGURATION_PROFIL_BUSINESS_WHATSAPP.md est créé THEN le document SHALL expliquer comment configurer le nom du chatbot, la photo de profil et la description business
4. WHEN les documents sont rédigés THEN le système SHALL utiliser le français avec des emojis pour la lisibilité

### Requirement 9: Suppression du Code Twilio

**User Story:** En tant que développeur, je veux que le code Twilio obsolète soit supprimé ou archivé, afin de maintenir une base de code propre.

#### Acceptance Criteria

1. WHEN la migration est terminée THEN le système SHALL archiver le fichier twilio_service.py dans le dossier services/archive/
2. WHEN les tests sont mis à jour THEN le système SHALL créer test_wassenger_service.py avec les mêmes cas de test adaptés
3. WHEN les imports sont mis à jour THEN le système SHALL remplacer toutes les références à twilio_service par wassenger_service
4. WHEN le fichier requirements.txt est mis à jour THEN le système SHALL remplacer la dépendance twilio par httpx (si non présent)

### Requirement 10: Configuration du Profil Business WhatsApp

**User Story:** En tant qu'administrateur, je veux configurer le profil business WhatsApp pour afficher un nom professionnel au lieu du numéro de téléphone, afin d'améliorer la confiance des contacts.

#### Acceptance Criteria

1. WHEN le compte WhatsApp Business est configuré THEN le système SHALL permettre de définir un nom d'entreprise visible par les contacts
2. WHEN une photo de profil est configurée THEN le système SHALL afficher cette photo aux contacts recevant des messages
3. WHEN la description business est configurée THEN le système SHALL afficher cette description quand un contact consulte le profil
4. WHEN le guide de configuration est créé THEN le document SHALL expliquer les différences entre WhatsApp Business App et WhatsApp Business API pour le masquage du numéro

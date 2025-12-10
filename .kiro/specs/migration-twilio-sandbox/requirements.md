# Document des Exigences - Migration Gupshup vers Twilio WhatsApp Sandbox 2025

## Introduction

Ce document définit les exigences pour la migration complète de l'intégration WhatsApp du système de chatbot existant. Le système actuel utilise Gupshup API (2025) et doit être migré vers Twilio WhatsApp Sandbox afin de permettre des tests gratuits d'envoi de messages via le dashboard de gestion.

L'objectif est de remplacer la couche d'intégration Gupshup par Twilio tout en conservant la même architecture globale, le frontend Next.js, la structure de la base de données Supabase, et la logique métier existante.

### Architecture Cible

```
Dashboard Admin (Next.js 14+)
         ↕
API REST Backend Python (FastAPI)
         ↕
Twilio WhatsApp Sandbox API ← NOUVELLE INTÉGRATION
         ↕
WhatsApp (via Twilio Sandbox)
         ↕
Base de données Supabase (PostgreSQL)
```

### Spécificités du Twilio WhatsApp Sandbox

Le Sandbox Twilio est un environnement de test gratuit avec les caractéristiques suivantes :
- **Gratuit** : Aucun frais pour les tests
- **Opt-in requis** : Les destinataires doivent rejoindre le Sandbox en envoyant un code
- **Numéro partagé** : Utilisation d'un numéro Twilio Sandbox (+14155238886)
- **Limitations de débit** : 1 message toutes les 3 secondes recommandé
- **Session 24h** : Les sessions expirent après 24 heures d'inactivité
- **Templates pré-approuvés** : Utilisation de templates Twilio prédéfinis

## Glossaire

- **Système** : L'ensemble de l'application comprenant le dashboard frontend et le backend API
- **Backend** : Le serveur API REST FastAPI
- **Twilio** : Plateforme de communication cloud fournissant l'accès à WhatsApp via Sandbox
- **Sandbox** : Environnement de test gratuit Twilio pour WhatsApp
- **Gupshup** : L'ancienne plateforme de messagerie (à remplacer)
- **Message 1** : Le message initial envoyé via un template WhatsApp
- **Message 2** : Le message de suivi automatique envoyé après interaction
- **Account SID** : Identifiant unique du compte Twilio
- **Auth Token** : Token d'authentification Twilio (secret)
- **Sandbox Number** : Numéro WhatsApp du Sandbox Twilio (+14155238886)
- **Join Code** : Code unique pour rejoindre le Sandbox (ex: "join <code>")
- **Webhook** : Endpoint HTTP recevant les notifications de Twilio
- **TwiML** : Langage de balisage Twilio pour les réponses webhook
- **Rate Limiting** : Limitation du nombre de requêtes (1 msg/3s pour Sandbox)

## Exigences

### Exigence 1 : Configuration Twilio

**User Story:** En tant que développeur, je veux configurer les nouvelles variables d'environnement Twilio, afin de permettre la connexion à l'API Twilio WhatsApp Sandbox.

#### Critères d'Acceptation

1. WHEN le Backend démarre THEN le Système SHALL charger les variables TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SANDBOX_NUMBER depuis le fichier .env
2. WHEN une variable Twilio obligatoire est manquante THEN le Backend SHALL afficher une erreur explicite au démarrage avec le nom de la variable manquante
3. WHEN les anciennes variables Gupshup sont présentes THEN le Système SHALL les ignorer sans erreur
4. WHEN la configuration est chargée THEN le Système SHALL initialiser le client Twilio avec les credentials fournis
5. WHEN le fichier .env.example est consulté THEN le Système SHALL documenter toutes les nouvelles variables Twilio avec des commentaires explicatifs en français

### Exigence 2 : Service Twilio - Envoi de Messages

**User Story:** En tant que système, je veux envoyer des messages WhatsApp via Twilio Sandbox API, afin de délivrer les messages aux contacts de test.

#### Critères d'Acceptation

1. WHEN un message est envoyé THEN le Backend SHALL utiliser la bibliothèque officielle twilio-python pour l'envoi
2. WHEN une requête message est construite THEN le Backend SHALL formater le numéro destinataire au format whatsapp:+XXXXXXXXXXX
3. WHEN le numéro source est utilisé THEN le Backend SHALL utiliser le numéro Sandbox Twilio configuré (whatsapp:+14155238886)
4. WHEN l'API Twilio retourne un SID de message THEN le Backend SHALL stocker ce SID et retourner un succès
5. WHEN l'API Twilio retourne une erreur THEN le Backend SHALL logger l'erreur avec le code et le message, puis retourner un échec avec les détails
6. WHEN un message est envoyé avec succès THEN le Backend SHALL mettre à jour le statut du message à "sent" avec l'horodatage

### Exigence 3 : Service Twilio - Envoi de Templates

**User Story:** En tant que système, je veux envoyer des messages templates via Twilio Sandbox, afin de délivrer le Message 1 aux contacts.

#### Critères d'Acceptation

1. WHEN un template Sandbox est envoyé THEN le Backend SHALL utiliser le Content SID du template Twilio pré-approuvé
2. WHEN des paramètres de template sont fournis THEN le Backend SHALL les passer via ContentVariables au format JSON
3. WHEN aucun template spécifique est demandé THEN le Backend SHALL utiliser le template par défaut "Your {{1}} code is {{2}}"
4. WHEN le template contient des variables THEN le Backend SHALL valider que tous les paramètres requis sont fournis
5. WHEN l'envoi du template réussit THEN le Backend SHALL retourner le Message SID Twilio

### Exigence 4 : Webhooks Twilio - Réception des Messages

**User Story:** En tant que système, je veux recevoir et traiter les webhooks Twilio pour les messages entrants, afin de déclencher l'automatisation du Message 2.

#### Critères d'Acceptation

1. WHEN un webhook Twilio est reçu THEN le Backend SHALL valider la signature Twilio pour sécuriser l'endpoint
2. WHEN un message entrant est reçu THEN le Backend SHALL extraire le numéro From, le Body et le MessageSid
3. WHEN le numéro expéditeur est extrait THEN le Backend SHALL rechercher le contact correspondant dans la base de données
4. WHEN un contact est trouvé avec un Message 1 récent THEN le Backend SHALL vérifier si le Message 2 doit être envoyé
5. WHEN le Message 2 doit être envoyé THEN le Backend SHALL créer une tâche Celery pour l'envoi automatique
6. WHEN le webhook est traité THEN le Backend SHALL retourner une réponse TwiML vide avec statut 200 OK

### Exigence 5 : Webhooks Twilio - Statuts de Livraison

**User Story:** En tant que système, je veux recevoir et traiter les webhooks Twilio pour les statuts de livraison, afin de mettre à jour le tracking des messages.

#### Critères d'Acceptation

1. WHEN un webhook de statut Twilio est reçu THEN le Backend SHALL extraire le MessageStatus (queued, sent, delivered, read, failed)
2. WHEN le MessageStatus est "delivered" THEN le Backend SHALL mettre à jour le statut du message à "delivered" avec l'horodatage
3. WHEN le MessageStatus est "read" THEN le Backend SHALL mettre à jour le statut du message à "read" avec l'horodatage
4. WHEN le MessageStatus est "failed" ou "undelivered" THEN le Backend SHALL marquer le message comme échoué et logger le ErrorCode
5. WHEN le MessageSid est présent THEN le Backend SHALL l'utiliser pour identifier le message dans la base de données
6. WHEN le statut est mis à jour THEN le Backend SHALL incrémenter les compteurs de la campagne correspondante

### Exigence 6 : Adaptation des Tâches Celery

**User Story:** En tant que système, je veux que les tâches Celery utilisent le nouveau service Twilio, afin de maintenir l'envoi asynchrone.

#### Critères d'Acceptation

1. WHEN une tâche d'envoi de campagne est exécutée THEN le Système SHALL utiliser twilio_service au lieu de gupshup_service
2. WHEN les messages sont envoyés en lot THEN le Système SHALL respecter la limite de 1 message toutes les 3 secondes pour le Sandbox
3. WHEN un message échoue THEN le Système SHALL programmer un retry avec délai exponentiel (60s, 120s, 240s)
4. WHEN le retry atteint 3 tentatives THEN le Système SHALL marquer le message comme définitivement échoué
5. WHEN un message réussit THEN le Système SHALL stocker le twilio_message_sid dans le champ whatsapp_message_id
6. WHEN la campagne est terminée THEN le Système SHALL mettre à jour les statistiques de la campagne

### Exigence 7 : Gestion des Limitations Sandbox

**User Story:** En tant que système, je veux gérer les limitations spécifiques du Twilio Sandbox, afin d'assurer un fonctionnement fiable.

#### Critères d'Acceptation

1. WHEN un message est envoyé à un numéro non inscrit au Sandbox THEN le Backend SHALL retourner une erreur explicite indiquant que le destinataire doit rejoindre le Sandbox
2. WHEN le rate limit Sandbox est atteint THEN le Backend SHALL attendre 3 secondes avant le prochain envoi
3. WHEN une session Sandbox expire (24h) THEN le Backend SHALL informer l'utilisateur que le destinataire doit renvoyer le code de join
4. WHEN le dashboard affiche les contacts THEN le Frontend SHALL indiquer visuellement les contacts inscrits au Sandbox
5. WHEN un envoi échoue avec l'erreur 63007 THEN le Backend SHALL identifier que le destinataire n'a pas rejoint le Sandbox

### Exigence 8 : Suppression de l'Intégration Gupshup

**User Story:** En tant que développeur, je veux supprimer complètement l'intégration Gupshup, afin de nettoyer le code et éviter toute confusion.

#### Critères d'Acceptation

1. WHEN le service gupshup_service.py est remplacé THEN le Système SHALL créer twilio_service.py avec une interface compatible
2. WHEN les imports sont mis à jour THEN le Système SHALL remplacer gupshup_service par twilio_service dans tous les fichiers
3. WHEN les variables d'environnement Gupshup sont supprimées THEN le Système SHALL retirer GUPSHUP_API_KEY, GUPSHUP_APP_NAME, GUPSHUP_PHONE_NUMBER de config.py
4. WHEN les fichiers de test Gupshup sont identifiés THEN le Système SHALL les supprimer ou les archiver
5. WHEN l'endpoint webhook Gupshup existe THEN le Système SHALL le supprimer et créer l'endpoint Twilio

### Exigence 9 : Interface Utilisateur Sandbox

**User Story:** En tant qu'utilisateur du dashboard, je veux voir les informations spécifiques au Sandbox Twilio, afin de comprendre comment tester l'envoi de messages.

#### Critères d'Acceptation

1. WHEN le dashboard de messages est affiché THEN le Frontend SHALL afficher un bandeau d'information sur le mode Sandbox
2. WHEN les instructions Sandbox sont affichées THEN le Frontend SHALL montrer le numéro Sandbox et le code de join
3. WHEN un contact n'est pas inscrit au Sandbox THEN le Frontend SHALL afficher un avertissement lors de la sélection
4. WHEN l'envoi échoue pour cause de non-inscription THEN le Frontend SHALL afficher un message explicatif avec les instructions de join
5. WHEN les limitations sont documentées THEN le Frontend SHALL afficher les restrictions (1 msg/3s, session 24h)

### Exigence 10 : Documentation Complète

**User Story:** En tant que développeur, je veux une documentation exhaustive en français, afin de configurer et utiliser le système avec Twilio Sandbox.

#### Critères d'Acceptation

1. WHEN la documentation Configuration_Twilio_WhatsApp_Sandbox_2025.md est consultée THEN le Système SHALL fournir un guide complet de configuration du dashboard Twilio
2. WHEN les credentials sont expliqués THEN le Système SHALL détailler où trouver Account SID, Auth Token et Sandbox Number dans l'interface Twilio 2025
3. WHEN le Sandbox est configuré THEN le Système SHALL expliquer comment activer le Sandbox, obtenir le code de join et tester l'adhésion
4. WHEN les webhooks sont configurés THEN le Système SHALL fournir les instructions pour configurer les URLs webhook avec ngrok en local
5. WHEN le troubleshooting est nécessaire THEN le Système SHALL lister les erreurs Twilio courantes (63007, 21608, etc.) et leurs solutions

### Exigence 11 : Documentation de Lancement Local

**User Story:** En tant que développeur, je veux un guide de lancement local complet, afin de tester l'envoi de messages en développement.

#### Critères d'Acceptation

1. WHEN le guide Guide_Configuration_Projet_Local_2025.md est consulté THEN le Système SHALL fournir les prérequis système (Python, Node.js, versions)
2. WHEN les dépendances sont installées THEN le Système SHALL documenter les commandes exactes pour backend et frontend
3. WHEN les variables d'environnement sont configurées THEN le Système SHALL fournir des exemples de fichiers .env complets
4. WHEN ngrok est configuré THEN le Système SHALL expliquer l'installation, le démarrage et la configuration des webhooks
5. WHEN le projet est démarré THEN le Système SHALL documenter l'ordre de démarrage et les commandes exactes
6. WHEN les tests sont effectués THEN le Système SHALL guider l'utilisateur pour tester l'envoi et la réception de messages

### Exigence 12 : Tests d'Intégration Twilio

**User Story:** En tant que développeur, je veux des tests pour valider l'intégration Twilio, afin de garantir le bon fonctionnement du système.

#### Critères d'Acceptation

1. WHEN un test de connexion Twilio est exécuté THEN le Système SHALL valider que les credentials sont corrects
2. WHEN un test d'envoi de message est exécuté THEN le Système SHALL valider le format de la requête Twilio
3. WHEN un test de webhook entrant est exécuté THEN le Système SHALL valider le parsing du payload Twilio
4. WHEN un test de webhook statut est exécuté THEN le Système SHALL valider la mise à jour des statuts
5. WHEN un test de validation de signature est exécuté THEN le Système SHALL vérifier la sécurité des webhooks


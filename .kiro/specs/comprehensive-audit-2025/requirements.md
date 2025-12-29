# Requirements Document

## Introduction

Ce document définit les exigences pour un audit complet et une optimisation de la plateforme de gestion de campagnes WhatsApp. L'objectif est de vérifier que toutes les fonctionnalités existantes fonctionnent correctement, d'identifier les problèmes de performance, et d'optimiser le système pour atteindre des temps de réponse exceptionnels.

**Important**: Ce projet est DÉJÀ FONCTIONNEL et DÉPLOYÉ. L'audit doit :
- ANALYSER le code existant (frontend + backend)
- IDENTIFIER les problèmes de performance
- VÉRIFIER que la logique métier fonctionne correctement
- OPTIMISER le code pour améliorer la vitesse
- CORRIGER les bugs et erreurs potentiels
- NETTOYER le code mort et les imports inutilisés

**Contrainte**: L'architecture et la structure du projet doivent rester intactes.

## Glossary

- **Message_1**: Premier message envoyé à un contact lors du lancement d'une campagne
- **Message_2**: Message de suivi envoyé uniquement si le contact interagit dans les 24h
- **Interaction**: Réponse du contact (texte, emoji, vocal, audio, image, vidéo, document)
- **Webhook**: Notification reçue de Wassenger lors d'événements WhatsApp
- **Optimistic_Update**: Mise à jour immédiate de l'UI avant confirmation serveur
- **TTI**: Time to Interactive - temps avant que la page soit interactive
- **FCP**: First Contentful Paint - temps avant le premier affichage de contenu
- **LCP**: Largest Contentful Paint - temps avant l'affichage du plus grand élément
- **Cache_Hit_Rate**: Pourcentage de requêtes servies depuis le cache

## Requirements

### Requirement 1: Performance de Chargement des Pages

**User Story:** As a user, I want all pages to load in under 300ms, so that I have a smooth and responsive experience.

#### Acceptance Criteria

1. THE Frontend SHALL afficher le Time to Interactive (TTI) en moins de 200ms
2. THE Frontend SHALL afficher le First Contentful Paint (FCP) en moins de 100ms
3. THE Frontend SHALL afficher le Largest Contentful Paint (LCP) en moins de 200ms
4. THE Frontend SHALL maintenir un bundle JavaScript inférieur à 200KB (gzipped)
5. WHEN une page est chargée, THE System SHALL afficher le contenu principal en moins de 300ms

### Requirement 2: Performance des Endpoints API

**User Story:** As a user, I want API responses to be instant, so that my actions are reflected immediately.

#### Acceptance Criteria

1. THE API SHALL répondre aux requêtes GET en moins de 50ms
2. THE API SHALL répondre aux requêtes POST/PUT/DELETE en moins de 100ms
3. THE API SHALL utiliser le cache Redis avec un hit rate supérieur à 80%
4. WHEN le cache est indisponible, THE API SHALL continuer à fonctionner en mode dégradé
5. THE API SHALL supporter la compression gzip pour les réponses volumineuses

### Requirement 3: Réactivité de l'Interface Utilisateur

**User Story:** As a user, I want the UI to update instantly when I perform actions, so that I see my changes immediately.

#### Acceptance Criteria

1. WHEN un contact est créé, THE UI SHALL afficher le nouveau contact en moins de 50ms (optimistic update)
2. WHEN un contact est supprimé, THE UI SHALL le retirer de la liste en moins de 50ms (optimistic update)
3. WHEN une erreur survient après un optimistic update, THE UI SHALL effectuer un rollback automatique
4. THE UI SHALL maintenir une fluidité de 60 FPS en toute circonstance
5. THE UI SHALL afficher les statistiques en moins de 100ms

### Requirement 4: Logique d'Envoi Message 1

**User Story:** As a campaign manager, I want Message 1 to be sent to all contacts when a campaign starts, so that I can reach my entire audience.

#### Acceptance Criteria

1. WHEN une campagne est lancée, THE System SHALL envoyer le Message 1 à TOUS les contacts de la campagne
2. WHEN un Message 1 est envoyé, THE System SHALL enregistrer le timestamp d'envoi (sent_at)
3. WHEN un Message 1 est envoyé, THE System SHALL démarrer un timer de 24h pour ce contact
4. THE System SHALL respecter le rate limiting de 1000 messages par jour
5. THE System SHALL logger chaque envoi de Message 1 pour traçabilité
6. IF un envoi échoue, THEN THE System SHALL réessayer jusqu'à 3 fois avec backoff exponentiel

### Requirement 5: Détection d'Interaction et Envoi Message 2

**User Story:** As a campaign manager, I want Message 2 to be sent immediately when a contact responds within 24h, so that I maintain engagement.

#### Acceptance Criteria

1. WHEN un webhook d'interaction est reçu, THE System SHALL vérifier si (current_time - sent_at) < 24 heures
2. IF l'interaction est dans les 24h ET aucun Message 2 n'a été envoyé, THEN THE System SHALL envoyer le Message 2 immédiatement
3. IF l'interaction est après 24h, THEN THE System SHALL NE PAS envoyer le Message 2
4. THE System SHALL détecter TOUS les types d'interactions: texte, emoji, vocal, audio, image, vidéo, document
5. THE System SHALL envoyer le Message 2 en moins de 5 secondes après détection de l'interaction
6. THE System SHALL enregistrer chaque interaction dans la table interactions

### Requirement 6: Prévention des Doublons Message 2

**User Story:** As a system, I want to prevent duplicate Message 2 from being sent, so that contacts don't receive the same message multiple times.

#### Acceptance Criteria

1. WHEN une interaction est reçue, THE System SHALL vérifier si un Message 2 existe déjà pour ce contact/campagne
2. IF un Message 2 existe déjà, THEN THE System SHALL ignorer les nouvelles interactions
3. THE System SHALL utiliser un verrou distribué Redis pour éviter les race conditions
4. THE System SHALL garantir l'idempotence: plusieurs interactions = 1 seul Message 2
5. THE System SHALL logger les tentatives de doublons pour audit

### Requirement 7: Clôture Automatique des Campagnes

**User Story:** As a campaign manager, I want campaigns to close automatically when all contacts are processed, so that I have accurate final statistics.

#### Acceptance Criteria

1. WHEN tous les contacts d'une campagne ont un état final, THE System SHALL marquer la campagne comme "completed"
2. THE System SHALL considérer comme état final: Message 2 envoyé, interaction tardive (>24h), aucune interaction (timeout 24h), échec définitif
3. WHEN une campagne est clôturée, THE System SHALL calculer et sauvegarder les statistiques finales
4. THE System SHALL exécuter une tâche périodique (toutes les heures) pour vérifier les timeouts 24h
5. THE System SHALL avoir un timeout de sécurité de 48h maximum pour toute campagne
6. THE System SHALL logger la clôture de chaque campagne avec les statistiques

### Requirement 8: Fonctionnement Autonome en Background

**User Story:** As a system administrator, I want the system to work autonomously without an admin connected, so that campaigns continue running 24/7.

#### Acceptance Criteria

1. THE System SHALL continuer à envoyer les Message 1 même si aucun admin n'est connecté
2. THE System SHALL continuer à traiter les webhooks même si aucun admin n'est connecté
3. THE System SHALL continuer à envoyer les Message 2 sur interaction même si aucun admin n'est connecté
4. THE Workers Celery SHALL avoir un uptime supérieur à 99.9%
5. IF un worker Celery crash, THEN THE System SHALL le redémarrer automatiquement
6. THE System SHALL envoyer des alertes si les workers sont down pendant plus de 5 minutes

### Requirement 9: Affichage des Statistiques en Temps Réel

**User Story:** As a campaign manager, I want to see real-time statistics, so that I can monitor campaign progress.

#### Acceptance Criteria

1. THE Dashboard SHALL afficher les statistiques en moins de 100ms
2. THE Dashboard SHALL afficher: total contacts, messages envoyés, messages délivrés, messages lus, interactions, échecs
3. WHEN un message est envoyé, THE Dashboard SHALL mettre à jour les compteurs en moins de 5 secondes
4. THE System SHALL utiliser des materialized views ou du cache pour les statistiques de grandes campagnes (>10k contacts)
5. THE System SHALL pré-calculer les statistiques lors de la clôture de campagne

### Requirement 10: Nettoyage du Code et Qualité

**User Story:** As a developer, I want clean and maintainable code, so that the project is easy to maintain and extend.

#### Acceptance Criteria

1. THE Codebase SHALL ne contenir aucun code mort ou commenté non documenté
2. THE Codebase SHALL ne contenir aucun import inutilisé
3. THE Codebase SHALL ne contenir aucun console.log/print de debug en production
4. THE Codebase SHALL passer tous les tests existants avec succès
5. THE Codebase SHALL avoir une couverture de tests supérieure à 80%
6. THE Codebase SHALL respecter les conventions de style (PEP 8 pour Python, ESLint pour TypeScript)


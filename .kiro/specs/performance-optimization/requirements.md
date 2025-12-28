# Requirements Document

## Introduction

Ce document définit les exigences pour l'optimisation des performances de l'application WhatsApp Chatbot. L'objectif est d'améliorer la réactivité de l'interface utilisateur, notamment la mise à jour rapide des statistiques après création de contacts, et d'ajouter une couche de cache applicatif utilisant Redis (Upstash).

**Important**: Upstash/Redis est déjà utilisé pour des fonctionnalités critiques :
- Gestion des tâches Celery (envoi de messages)
- Envoi du deuxième message après interactions
- Mise à jour des statuts de messages
- Compteurs de monitoring quotidiens

L'optimisation doit **préserver** ces fonctionnalités existantes et ajouter une couche de cache **séparée** pour les données fréquemment lues.

## Glossary

- **Cache_Service**: Service de mise en cache utilisant Redis/Upstash pour stocker les données fréquemment accédées
- **Stats_Endpoint**: Endpoint API qui retourne les statistiques agrégées (contacts, messages, campagnes)
- **Query_Client**: Instance TanStack Query côté frontend gérant le cache des requêtes API
- **Invalidation**: Processus de suppression ou mise à jour des données en cache après modification
- **TTL**: Time To Live - durée de validité d'une entrée en cache
- **Optimistic_Update**: Mise à jour immédiate de l'UI avant confirmation serveur

## Requirements

### Requirement 1: Cache Backend pour les Statistiques

**User Story:** As a user, I want statistics to load instantly, so that I can see dashboard data without waiting.

#### Acceptance Criteria

1. THE Cache_Service SHALL cache les résultats de `/messages/stats` avec un TTL de 60 secondes
2. THE Cache_Service SHALL cache les comptages de contacts par catégorie avec un TTL de 60 secondes
3. WHEN un contact est créé, modifié ou supprimé, THE Cache_Service SHALL invalider les caches de statistiques concernés
4. WHEN une catégorie est modifiée, THE Cache_Service SHALL invalider le cache des catégories
5. THE Stats_Endpoint SHALL retourner les données en moins de 200ms en utilisant le cache

### Requirement 2: Optimisation des Requêtes Frontend

**User Story:** As a user, I want the UI to update immediately after I create a contact, so that I see my changes reflected instantly.

#### Acceptance Criteria

1. WHEN un contact est créé avec succès, THE Query_Client SHALL effectuer une mise à jour optimiste des statistiques
2. THE Query_Client SHALL utiliser un staleTime de 5 minutes pour les données de statistiques
3. THE Query_Client SHALL utiliser un staleTime de 2 minutes pour les listes de contacts et catégories
4. WHEN une mutation réussit, THE Query_Client SHALL invalider uniquement les caches directement affectés
5. THE Query_Client SHALL implémenter le refetch en arrière-plan sans bloquer l'UI

### Requirement 3: Cache Redis Optimisé pour Upstash (Sans Impact sur Celery)

**User Story:** As a developer, I want efficient Redis usage for caching, so that I minimize Upstash costs while preserving existing Celery/messaging functionality.

#### Acceptance Criteria

1. THE Cache_Service SHALL utiliser des clés Redis avec préfixes dédiés (cache:stats:*, cache:categories:*) séparés des clés Celery existantes
2. THE Cache_Service SHALL implémenter une stratégie de cache-aside (lecture du cache, fallback sur DB)
3. THE Cache_Service SHALL utiliser des pipelines Redis pour les opérations multiples de lecture
4. WHEN le cache est indisponible, THE Cache_Service SHALL continuer à fonctionner en mode dégradé (requêtes DB directes)
5. THE Cache_Service SHALL NE PAS interférer avec les clés existantes (whatsapp:*, campaign:*, celery*)
6. THE Cache_Service SHALL réutiliser la connexion Redis existante du MonitoringService

### Requirement 4: Invalidation Intelligente du Cache

**User Story:** As a user, I want my data to be consistent, so that I always see accurate information.

#### Acceptance Criteria

1. WHEN un contact est créé, THE Cache_Service SHALL invalider: stats globales, comptage catégories associées
2. WHEN un contact est supprimé, THE Cache_Service SHALL invalider: stats globales, comptage catégories associées
3. WHEN une catégorie est modifiée, THE Cache_Service SHALL invalider: liste catégories, détail catégorie
4. WHEN un message est envoyé, THE Cache_Service SHALL invalider: stats messages, compteurs monitoring
5. THE Cache_Service SHALL supporter l'invalidation par pattern (cache:stats:*)

### Requirement 5: Optimisation des Endpoints Lents

**User Story:** As a user, I want all pages to load quickly, so that I have a smooth experience.

#### Acceptance Criteria

1. THE Stats_Endpoint SHALL agréger les comptages en une seule requête SQL au lieu de requêtes multiples
2. THE Categories_Endpoint SHALL inclure le contact_count dans la requête principale (JOIN)
3. THE Messages_Endpoint SHALL limiter le chargement des relations (lazy loading pour contact/campaign details)
4. WHEN la pagination est utilisée, THE API SHALL retourner uniquement les champs nécessaires
5. THE API SHALL supporter la compression gzip pour les réponses volumineuses

### Requirement 6: Monitoring et Métriques de Performance

**User Story:** As a developer, I want to monitor cache performance, so that I can identify and fix bottlenecks.

#### Acceptance Criteria

1. THE Cache_Service SHALL exposer un endpoint `/api/cache/stats` avec les métriques (hits, misses, latency)
2. THE Cache_Service SHALL logger les opérations de cache avec leur durée
3. WHEN le taux de cache miss dépasse 50%, THE System SHALL logger un warning
4. THE System SHALL mesurer et logger le temps de réponse des endpoints critiques
5. THE Monitoring_Dashboard SHALL afficher les métriques de cache en temps réel (optionnel)

### Requirement 7: Gestion des Échecs de Campagne (24h sans interaction)

**User Story:** As a campaign manager, I want contacts without interaction after 24h to be marked as failed, so that I have accurate campaign statistics.

#### Acceptance Criteria

1. THE System SHALL exécuter une tâche périodique toutes les heures pour vérifier les messages sans interaction
2. WHEN un Message 1 a été envoyé il y a plus de 24h ET le contact n'a pas interagi, THE System SHALL marquer le message comme "no_interaction"
3. WHEN un message est marqué "no_interaction", THE System SHALL incrémenter le compteur d'échecs de la campagne
4. THE System SHALL mettre à jour les statistiques de la campagne (failed_count) après chaque vérification
5. WHEN tous les messages d'une campagne sont soit "delivered/read" soit "no_interaction", THE System SHALL marquer la campagne comme "completed"
6. THE System SHALL logger chaque contact marqué comme "no_interaction" pour traçabilité

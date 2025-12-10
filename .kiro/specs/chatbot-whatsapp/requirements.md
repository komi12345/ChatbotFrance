# Document des Exigences - Chatbot WhatsApp

## Introduction

Ce document définit les exigences fonctionnelles et non-fonctionnelles pour un système complet de chatbot WhatsApp avec dashboard d'administration. Le système permettra aux administrateurs de gérer des contacts, créer des catégories, envoyer des campagnes de messages automatisés via WhatsApp Business API, et suivre les statistiques d'engagement en temps réel.

Le système comprend deux composants principaux :
- Un dashboard web d'administration développé avec Next.js 14+
- Un backend API REST développé avec FastAPI (Python)

L'intégration avec WhatsApp Business API (Meta Cloud API) permettra l'envoi de messages, la réception de webhooks pour les interactions, et le tracking complet des campagnes.

## Glossaire

- **Système** : L'ensemble de l'application comprenant le dashboard frontend et le backend API
- **Dashboard** : L'interface web d'administration Next.js
- **Backend** : Le serveur API REST FastAPI
- **Super Admin** : Utilisateur avec accès complet incluant la gestion des comptes Admin
- **Admin** : Utilisateur avec accès au dashboard mais sans gestion d'autres utilisateurs
- **Contact** : Un numéro WhatsApp enregistré dans le système
- **Catégorie** : Un groupe de contacts partageant des caractéristiques communes
- **Message 1** : Le message initial envoyé via un template WhatsApp approuvé
- **Message 2** : Le message de suivi automatique envoyé après interaction
- **Campagne** : Un envoi de messages à une ou plusieurs catégories
- **Interaction** : Une réponse ou action d'un contact sur WhatsApp
- **Template WhatsApp** : Un modèle de message pré-approuvé par Meta
- **Webhook** : Un endpoint HTTP recevant les notifications de WhatsApp
- **RLS** : Row Level Security - Sécurité au niveau des lignes dans Supabase
- **Supabase** : La plateforme de base de données PostgreSQL utilisée
- **Meta Cloud API** : L'API officielle de WhatsApp Business de Meta
- **Indicatif Pays** : Le code téléphonique international (ex: +33, +1)
- **Rate Limiting** : Limitation du nombre de requêtes par unité de temps
- **Retry** : Nouvelle tentative d'envoi après un échec
- **JWT** : JSON Web Token - Mécanisme d'authentification
- **Celery** : Système de gestion de tâches asynchrones
- **Redis** : Base de données en mémoire utilisée comme message broker

## Exigences

### Exigence 1 : Authentification et Gestion des Utilisateurs

**User Story:** En tant qu'administrateur système, je veux un système d'authentification sécurisé avec deux niveaux d'accès, afin de contrôler les permissions et protéger les données sensibles.

#### Critères d'Acceptation

1. WHEN un utilisateur soumet des identifiants valides THEN le Système SHALL générer un JWT avec une durée de validité de 30 minutes
2. WHEN un Super Admin accède au dashboard THEN le Système SHALL afficher la section de gestion des utilisateurs Admin
3. WHEN un Admin accède au dashboard THEN le Système SHALL masquer la section de gestion des utilisateurs
4. WHEN un Super Admin crée un compte Admin THEN le Système SHALL hasher le mot de passe avec bcrypt et stocker les identifiants dans Supabase
5. WHEN un utilisateur tente d'accéder à une ressource sans JWT valide THEN le Système SHALL retourner une erreur 401 Unauthorized
6. WHEN les règles RLS de Supabase sont appliquées THEN le Système SHALL garantir qu'un Admin ne peut accéder qu'à ses propres données

### Exigence 2 : Gestion des Contacts

**User Story:** En tant qu'Admin, je veux gérer une base de contacts WhatsApp avec leurs indicatifs pays, afin d'organiser mes destinataires de campagnes.

#### Critères d'Acceptation

1. WHEN un Admin ajoute un contact THEN le Système SHALL valider le format du numéro avec l'indicatif pays complet
2. WHEN un Admin sélectionne un indicatif pays THEN le Système SHALL afficher une liste déroulante avec le format "+XX Pays"
3. WHEN un Admin importe un fichier CSV de contacts THEN le Système SHALL valider chaque ligne et créer les contacts valides
4. WHEN un contact est créé THEN le Système SHALL stocker le numéro avec l'indicatif pays dans la table contacts de Supabase
5. WHEN un Admin supprime un contact THEN le Système SHALL retirer toutes les associations avec les catégories
6. WHEN un Admin modifie un contact THEN le Système SHALL mettre à jour les informations et conserver l'historique des campagnes

### Exigence 3 : Gestion des Catégories

**User Story:** En tant qu'Admin, je veux créer et gérer des catégories de contacts, afin de segmenter mes audiences pour les campagnes ciblées.

#### Critères d'Acceptation

1. WHEN un Admin crée une catégorie THEN le Système SHALL enregistrer le nom personnalisé dans la table categories
2. WHEN un Admin ajoute un contact à une catégorie THEN le Système SHALL créer une relation dans la table category_contacts
3. WHEN un contact est associé à plusieurs catégories THEN le Système SHALL permettre les associations multiples via la relation many-to-many
4. WHEN un Admin consulte une catégorie THEN le Système SHALL afficher le nombre total de contacts associés
5. WHEN un Admin supprime une catégorie THEN le Système SHALL retirer toutes les associations mais conserver les contacts
6. WHEN la page catégories est affichée THEN le Système SHALL présenter chaque catégorie avec un gradient de couleur unique

### Exigence 4 : Configuration et Envoi de Messages

**User Story:** En tant qu'Admin, je veux configurer deux types de messages et les envoyer automatiquement selon une logique définie, afin d'automatiser mes communications WhatsApp.

#### Critères d'Acceptation

1. WHEN un Admin configure le Message 1 THEN le Système SHALL utiliser un template WhatsApp pré-approuvé par Meta
2. WHEN un Admin configure le Message 2 THEN le Système SHALL stocker le contenu comme message de suivi automatique
3. WHEN un Admin insère un lien dans un message THEN le Système SHALL valider le format URL et permettre les liens wa.me
4. WHEN un Admin envoie le Message 1 à une catégorie THEN le Système SHALL créer une tâche Celery pour l'envoi massif
5. WHEN un contact répond après avoir reçu le Message 1 THEN le Système SHALL déclencher automatiquement l'envoi du Message 2
6. WHEN un contact continue d'interagir THEN le Système SHALL continuer d'envoyer le Message 2 pour chaque interaction
7. WHEN un Admin envoie un nouveau Message 1 THEN le Système SHALL réinitialiser la séquence d'automatisation pour les contacts ciblés
8. WHEN le Système envoie des messages THEN le Système SHALL respecter la limite de 25 messages par minute de l'API WhatsApp

### Exigence 5 : Prévisualisation des Messages

**User Story:** En tant qu'Admin, je veux prévisualiser mes messages avant l'envoi, afin de vérifier le contenu et le formatage.

#### Critères d'Acceptation

1. WHEN un Admin saisit un message THEN le Système SHALL afficher une prévisualisation en temps réel dans l'interface
2. WHEN un message contient un lien THEN le Système SHALL afficher le lien comme cliquable dans la prévisualisation
3. WHEN un Admin modifie le contenu THEN le Système SHALL mettre à jour la prévisualisation instantanément

### Exigence 6 : Tracking et Statistiques des Campagnes

**User Story:** En tant qu'Admin, je veux suivre les performances de mes campagnes en temps réel, afin d'analyser l'efficacité de mes communications.

#### Critères d'Acceptation

1. WHEN un message est envoyé THEN le Système SHALL enregistrer le statut dans la table messages avec l'horodatage
2. WHEN une campagne est terminée THEN le Système SHALL calculer le nombre total de messages envoyés
3. WHEN le dashboard statistiques est affiché THEN le Système SHALL présenter le nombre de messages réussis avec détails par contact
4. WHEN des messages échouent THEN le Système SHALL enregistrer la raison de l'échec pour chaque contact
5. WHEN le taux de réussite est calculé THEN le Système SHALL diviser les messages réussis par le total et afficher en pourcentage
6. WHEN une interaction est reçue THEN le Système SHALL incrémenter le compteur d'interactions pour la campagne
7. WHEN le dashboard est consulté THEN le Système SHALL afficher des graphiques d'évolution des envois avec Recharts
8. WHEN un Admin exporte les statistiques THEN le Système SHALL générer un fichier CSV avec toutes les données de campagne

### Exigence 7 : Système de Retry Automatique

**User Story:** En tant qu'Admin, je veux que le système réessaie automatiquement les envois échoués, afin de maximiser le taux de livraison des messages.

#### Critères d'Acceptation

1. WHEN un message échoue lors de l'envoi THEN le Système SHALL programmer une nouvelle tentative automatique
2. WHEN le Système effectue un retry THEN le Système SHALL appliquer un délai exponentiel entre les tentatives
3. WHEN un message a échoué 3 fois THEN le Système SHALL marquer le message comme définitivement échoué
4. WHEN un retry échoue THEN le Système SHALL logger l'échec avec l'horodatage et la raison dans les logs
5. WHEN un message réussit après retry THEN le Système SHALL mettre à jour le statut à "réussi" dans la table messages

### Exigence 8 : Réception et Traitement des Webhooks

**User Story:** En tant que système, je veux recevoir et traiter les webhooks WhatsApp en temps réel, afin de déclencher les automatisations appropriées.

#### Critères d'Acceptation

1. WHEN un webhook WhatsApp est reçu THEN le Backend SHALL valider le token de vérification
2. WHEN un webhook contient une interaction client THEN le Backend SHALL enregistrer l'interaction dans la table interactions
3. WHEN une interaction est enregistrée THEN le Backend SHALL vérifier si le contact doit recevoir le Message 2
4. WHEN le Message 2 doit être envoyé THEN le Backend SHALL créer une tâche Celery pour l'envoi
5. WHEN le webhook est traité THEN le Backend SHALL retourner un statut 200 OK dans les 20 secondes
6. WHEN le traitement du webhook échoue THEN le Backend SHALL logger l'erreur sans bloquer la réponse HTTP

### Exigence 9 : Dashboard Statistiques et Visualisations

**User Story:** En tant qu'Admin, je veux visualiser des graphiques et métriques clés sur un dashboard, afin de comprendre rapidement les performances globales.

#### Critères d'Acceptation

1. WHEN le dashboard est affiché THEN le Système SHALL présenter le nombre total de messages envoyés
2. WHEN le dashboard est affiché THEN le Système SHALL afficher le taux de réussite global en pourcentage
3. WHEN le dashboard est affiché THEN le Système SHALL montrer le nombre d'utilisateurs actifs
4. WHEN le dashboard est affiché THEN le Système SHALL calculer et afficher le coût estimé des envois
5. WHEN le graphique d'évolution est affiché THEN le Système SHALL présenter le volume de messages par jour sur 7 jours
6. WHEN le graphique de répartition est affiché THEN le Système SHALL montrer les statuts en diagramme circulaire
7. WHEN l'historique des messages est consulté THEN le Système SHALL permettre la recherche par expéditeur
8. WHEN l'historique est filtré THEN le Système SHALL permettre le filtrage par statut avec pagination

### Exigence 10 : Sécurité et Validation des Données

**User Story:** En tant que système, je veux valider toutes les entrées utilisateur et sécuriser les accès, afin de protéger l'intégrité des données et prévenir les attaques.

#### Critères d'Acceptation

1. WHEN des données sont soumises au Backend THEN le Système SHALL valider les données avec Pydantic schemas
2. WHEN des données sont soumises au Dashboard THEN le Système SHALL valider les formulaires avec React Hook Form
3. WHEN un mot de passe est créé THEN le Système SHALL hasher le mot de passe avec bcrypt avant stockage
4. WHEN une requête API est reçue THEN le Backend SHALL vérifier la présence et validité du JWT
5. WHEN une requête cross-origin est reçue THEN le Backend SHALL appliquer la politique CORS configurée
6. WHEN un numéro de téléphone est saisi THEN le Système SHALL valider le format avec l'indicatif pays
7. WHEN une URL est insérée dans un message THEN le Système SHALL valider le format URL

### Exigence 11 : Performance et Optimisation

**User Story:** En tant qu'utilisateur du système, je veux des temps de réponse rapides et une interface fluide, afin d'avoir une expérience utilisateur optimale.

#### Critères d'Acceptation

1. WHEN une liste de contacts est affichée THEN le Système SHALL implémenter la pagination avec maximum 50 éléments par page
2. WHEN une requête base de données est exécutée THEN le Système SHALL utiliser les index sur les colonnes fréquemment requêtées
3. WHEN des requêtes multiples sont nécessaires THEN le Système SHALL optimiser avec des jointures SQL appropriées
4. WHEN l'API reçoit des requêtes THEN le Backend SHALL appliquer un rate limiting de 100 requêtes par minute par utilisateur
5. WHEN le Dashboard charge des données THEN le Système SHALL utiliser React Query pour le caching et la synchronisation

### Exigence 12 : Gestion des Erreurs et Logging

**User Story:** En tant que développeur, je veux un système complet de gestion d'erreurs et de logging, afin de diagnostiquer et résoudre rapidement les problèmes.

#### Critères d'Acceptation

1. WHEN une erreur survient dans le Backend THEN le Système SHALL capturer l'exception avec un bloc try-except
2. WHEN une erreur est capturée THEN le Système SHALL logger l'erreur avec le niveau approprié et le contexte
3. WHEN une erreur API est retournée THEN le Système SHALL inclure un message d'erreur clair et un code HTTP approprié
4. WHEN une erreur survient dans le Dashboard THEN le Système SHALL afficher un message d'erreur compréhensible à l'utilisateur
5. WHEN une action importante est effectuée THEN le Système SHALL logger l'action avec l'utilisateur et l'horodatage
6. WHEN un envoi de message échoue THEN le Système SHALL logger les détails de l'échec pour analyse ultérieure

### Exigence 13 : Interface Utilisateur Responsive

**User Story:** En tant qu'Admin, je veux accéder au dashboard depuis différents appareils, afin de gérer mes campagnes en mobilité.

#### Critères d'Acceptation

1. WHEN le Dashboard est affiché sur mobile THEN le Système SHALL adapter la mise en page avec Tailwind CSS responsive
2. WHEN le Dashboard est affiché sur tablette THEN le Système SHALL ajuster les composants pour une utilisation tactile
3. WHEN le Dashboard est affiché sur desktop THEN le Système SHALL utiliser pleinement l'espace disponible
4. WHEN un formulaire est affiché THEN le Système SHALL garantir l'accessibilité des champs sur tous les appareils
5. WHEN des graphiques sont affichés THEN le Système SHALL adapter la taille des graphiques Recharts à l'écran

### Exigence 14 : Indicateurs de Chargement et Feedback Utilisateur

**User Story:** En tant qu'Admin, je veux des indicateurs visuels pendant les opérations, afin de comprendre l'état du système.

#### Critères d'Acceptation

1. WHEN une requête API est en cours THEN le Dashboard SHALL afficher un indicateur de chargement
2. WHEN une opération réussit THEN le Dashboard SHALL afficher un message de succès temporaire
3. WHEN une opération échoue THEN le Dashboard SHALL afficher un message d'erreur explicite
4. WHEN un envoi massif est en cours THEN le Dashboard SHALL afficher une barre de progression
5. WHEN des données sont en cours de chargement THEN le Dashboard SHALL afficher des skeleton loaders

### Exigence 15 : Configuration et Variables d'Environnement

**User Story:** En tant que développeur, je veux configurer facilement les différents environnements, afin de déployer le système en local et en production.

#### Critères d'Acceptation

1. WHEN le Backend démarre THEN le Système SHALL charger les variables d'environnement depuis le fichier .env
2. WHEN une variable d'environnement est manquante THEN le Backend SHALL afficher une erreur explicite au démarrage
3. WHEN le Dashboard démarre THEN le Système SHALL charger les variables depuis .env.local
4. WHEN les identifiants WhatsApp sont configurés THEN le Backend SHALL valider la connexion à l'API Meta au démarrage
5. WHEN la connexion Supabase est configurée THEN le Système SHALL vérifier la connectivité à la base de données

### Exigence 16 : Tâches Asynchrones avec Celery

**User Story:** En tant que système, je veux traiter les envois massifs de manière asynchrone, afin de ne pas bloquer l'interface utilisateur.

#### Critères d'Acceptation

1. WHEN un envoi massif est déclenché THEN le Backend SHALL créer une tâche Celery pour le traitement
2. WHEN une tâche Celery est créée THEN le Système SHALL retourner immédiatement un identifiant de tâche à l'utilisateur
3. WHEN une tâche Celery s'exécute THEN le Système SHALL traiter les envois par lots de 25 messages par minute
4. WHEN une tâche Celery se termine THEN le Système SHALL mettre à jour le statut de la campagne dans la base de données
5. WHEN Redis est indisponible THEN le Backend SHALL logger une erreur critique et refuser les nouvelles tâches

### Exigence 17 : Intégration WhatsApp Business API

**User Story:** En tant que système, je veux communiquer avec l'API WhatsApp Business de Meta, afin d'envoyer et recevoir des messages.

#### Critères d'Acceptation

1. WHEN un message est envoyé THEN le Backend SHALL utiliser l'endpoint Meta Cloud API avec le Phone Number ID
2. WHEN un message est envoyé THEN le Backend SHALL inclure l'Access Token dans les headers d'autorisation
3. WHEN un template est utilisé THEN le Backend SHALL formater la requête selon les spécifications Meta
4. WHEN l'API WhatsApp retourne une erreur THEN le Backend SHALL parser le code d'erreur et logger les détails
5. WHEN un webhook est configuré THEN le Backend SHALL exposer un endpoint POST pour recevoir les notifications
6. WHEN un webhook est vérifié par Meta THEN le Backend SHALL répondre avec le challenge token

### Exigence 18 : Base de Données et Migrations

**User Story:** En tant que développeur, je veux une structure de base de données bien définie avec des migrations, afin de maintenir la cohérence des données.

#### Critères d'Acceptation

1. WHEN la base de données est initialisée THEN le Système SHALL exécuter le script schema.sql pour créer les tables
2. WHEN les tables sont créées THEN le Système SHALL définir les clés primaires et étrangères appropriées
3. WHEN les relations sont définies THEN le Système SHALL créer les tables de jonction pour les relations many-to-many
4. WHEN les RLS sont configurés THEN le Système SHALL appliquer les politiques de sécurité au niveau des lignes
5. WHEN un Super Admin est nécessaire THEN le Système SHALL exécuter seed_superadmin.sql pour l'injection
6. WHEN un Admin de test est nécessaire THEN le Système SHALL exécuter seed_admin.sql pour l'injection

### Exigence 19 : Documentation et Guides de Déploiement

**User Story:** En tant que développeur, je veux une documentation complète, afin de configurer, tester et déployer le système facilement.

#### Critères d'Acceptation

1. WHEN la documentation est consultée THEN le Système SHALL fournir un guide de configuration complet dans 01-CONFIGURATION.md
2. WHEN l'intégration WhatsApp est nécessaire THEN le Système SHALL fournir un guide détaillé dans 02-WHATSAPP-SETUP.md
3. WHEN le test en local est requis THEN le Système SHALL fournir les instructions dans 03-LANCEMENT-LOCAL.md
4. WHEN le déploiement est nécessaire THEN le Système SHALL fournir un guide de déploiement gratuit dans 04-DEPLOIEMENT-GRATUIT.md
5. WHEN les fichiers .env sont configurés THEN le Système SHALL fournir des fichiers .env.example avec toutes les variables

### Exigence 20 : Gestion des Campagnes

**User Story:** En tant qu'Admin, je veux créer et gérer des campagnes d'envoi, afin d'organiser mes communications WhatsApp.

#### Critères d'Acceptation

1. WHEN un Admin crée une campagne THEN le Système SHALL enregistrer le nom, la date et les catégories cibles
2. WHEN une campagne est lancée THEN le Système SHALL créer les enregistrements de messages pour tous les contacts des catégories
3. WHEN une campagne est consultée THEN le Système SHALL afficher le statut global et les statistiques détaillées
4. WHEN une campagne est terminée THEN le Système SHALL calculer et afficher le taux de réussite final
5. WHEN l'historique des campagnes est affiché THEN le Système SHALL lister toutes les campagnes avec pagination

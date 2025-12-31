# 📱 Documentation Complète du Projet WhatsApp Chatbot 2025

## 🎯 Prompt de Création du Projet

> **Créer une plateforme complète de gestion de campagnes WhatsApp** permettant l'envoi automatisé de messages à des contacts organisés par catégories, avec suivi en temps réel, système de Message 1 / Message 2 basé sur les interactions, et respect des limites d'envoi pour éviter les bans WhatsApp.

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture Technique](#architecture-technique)
3. [Stack Technologique](#stack-technologique)
4. [Structure du Projet](#structure-du-projet)
5. [Base de Données](#base-de-données)
6. [Backend - API FastAPI](#backend---api-fastapi)
7. [Frontend - Next.js](#frontend---nextjs)
8. [Système d'Envoi de Messages](#système-denvoi-de-messages)
9. [Tâches Celery](#tâches-celery)
10. [Intégration Wassenger](#intégration-wassenger)
11. [Webhooks](#webhooks)
12. [Configuration et Déploiement](#configuration-et-déploiement)
13. [Guide d'Installation](#guide-dinstallation)
14. [Design UI/UX](#design-uiux)

---

## 🎯 Vue d'Ensemble

### Objectif du Projet

Cette plateforme permet de :
- **Gérer des contacts** avec vérification WhatsApp automatique
- **Organiser les contacts** en catégories
- **Créer des campagnes** d'envoi de messages en masse
- **Envoyer des messages** via l'API Wassenger (WhatsApp)
- **Suivre les interactions** en temps réel (envoyé, délivré, lu, réponse)
- **Automatiser le Message 2** basé sur les réponses des contacts

### Logique Message 1 / Message 2

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUX DE CAMPAGNE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Création de campagne avec Message 1 et Message 2        │
│                                                             │
│  2. Envoi du Message 1 à tous les contacts                  │
│     └── Délai de 5 secondes entre chaque message            │
│     └── Lots de 50 messages avec pause de 60 secondes       │
│                                                             │
│  3. Attente des réponses (24h maximum)                      │
│     ├── SI le contact répond dans les 24h :                 │
│     │   └── Message 2 envoyé IMMÉDIATEMENT                  │
│     │                                                       │
│     └── SI le contact ne répond PAS dans les 24h :          │
│         └── Message 2 N'EST PAS envoyé                      │
│         └── Campagne terminée pour ce contact               │
│                                                             │
│  4. Campagne complète quand tous les contacts ont terminé   │
│     leur cycle (Message 2 envoyé OU 24h sans réponse)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE GLOBALE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │   Frontend   │────▶│   Backend    │────▶│   Supabase   │         │
│  │   Next.js    │     │   FastAPI    │     │  PostgreSQL  │         │
│  │   React 19   │     │   Python     │     │              │         │
│  └──────────────┘     └──────────────┘     └──────────────┘         │
│         │                    │                    │                  │
│         │                    ▼                    │                  │
│         │             ┌──────────────┐            │                  │
│         │             │    Celery    │            │                  │
│         │             │   Workers    │            │                  │
│         │             └──────────────┘            │                  │
│         │                    │                    │                  │
│         │                    ▼                    │                  │
│         │             ┌──────────────┐            │                  │
│         │             │    Redis     │            │                  │
│         │             │   (Queue)    │            │                  │
│         │             └──────────────┘            │                  │
│         │                    │                    │                  │
│         │                    ▼                    │                  │
│         │             ┌──────────────┐            │                  │
│         └────────────▶│  Wassenger   │◀───────────┘                  │
│                       │  WhatsApp    │                               │
│                       │     API      │                               │
│                       └──────────────┘                               │
│                              │                                       │
│                              ▼                                       │
│                       ┌──────────────┐                               │
│                       │   Webhooks   │                               │
│                       │  (Statuts)   │                               │
│                       └──────────────┘                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Technologique

### Backend (Python 3.11+)

| Package | Version | Description |
|---------|---------|-------------|
| `fastapi` | ≥0.109.0 | Framework API REST moderne et performant |
| `uvicorn[standard]` | ≥0.27.0 | Serveur ASGI pour FastAPI |
| `celery` | ≥5.3.6 | File d'attente de tâches asynchrones |
| `redis` | ≥5.0.1 | Broker pour Celery + Cache |
| `supabase` | ≥2.3.4 | Client Supabase (PostgreSQL) |
| `pydantic` | ≥2.5.3 | Validation des données |
| `pydantic-settings` | ≥2.1.0 | Gestion des variables d'environnement |
| `python-jose[cryptography]` | ≥3.3.0 | JWT pour l'authentification |
| `passlib[bcrypt]` | ≥1.7.4 | Hachage des mots de passe |
| `httpx` | ≥0.26.0 | Client HTTP async pour Wassenger |
| `phonenumbers` | ≥8.13.27 | Validation des numéros de téléphone |
| `slowapi` | ≥0.1.9 | Rate limiting |
| `pytest` | ≥7.4.4 | Tests unitaires |
| `hypothesis` | ≥6.92.0 | Property-based testing |

### Frontend (Node.js 18+)

| Package | Version | Description |
|---------|---------|-------------|
| `next` | ^16.1.0 | Framework React avec App Router |
| `react` | 19.2.0 | Bibliothèque UI |
| `typescript` | ^5.9.3 | Typage statique |
| `@tanstack/react-query` | ^5.90.11 | Gestion du cache et des requêtes |
| `axios` | ^1.13.2 | Client HTTP |
| `tailwindcss` | ^4 | Framework CSS utilitaire |
| `zod` | ^4.1.13 | Validation des schémas |
| `react-hook-form` | ^7.66.1 | Gestion des formulaires |
| `recharts` | ^3.5.0 | Graphiques et statistiques |
| `lucide-react` | ^0.555.0 | Icônes |
| `@radix-ui/*` | latest | Composants UI accessibles |
| `vitest` | ^4.0.15 | Tests unitaires |
| `fast-check` | ^4.4.0 | Property-based testing |

### Infrastructure

| Service | Description |
|---------|-------------|
| **Supabase** | Base de données PostgreSQL + Auth |
| **Redis** | File d'attente Celery + Cache |
| **Wassenger** | API WhatsApp Business |
| **Render** | Hébergement Backend |
| **Netlify** | Hébergement Frontend |

---

## 📁 Structure du Projet

```
projet/
├── backend/                          # API FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # Point d'entrée FastAPI
│   │   ├── config.py                 # Configuration (variables d'env)
│   │   ├── database.py               # Connexion DB (legacy)
│   │   ├── supabase_client.py        # Client Supabase
│   │   │
│   │   ├── routers/                  # Endpoints API
│   │   │   ├── auth.py               # Authentification JWT
│   │   │   ├── users.py              # Gestion utilisateurs
│   │   │   ├── contacts.py           # CRUD contacts
│   │   │   ├── categories.py         # CRUD catégories
│   │   │   ├── campaigns.py          # CRUD campagnes
│   │   │   ├── messages.py           # Gestion messages
│   │   │   ├── webhooks.py           # Webhooks Wassenger
│   │   │   ├── verify.py             # Vérification WhatsApp
│   │   │   ├── monitoring.py         # Monitoring quotas
│   │   │   └── cache.py              # Gestion cache
│   │   │
│   │   ├── services/                 # Logique métier
│   │   │   ├── auth_service.py       # Service authentification
│   │   │   ├── wassenger_service.py  # Intégration Wassenger
│   │   │   ├── message_service.py    # Service messages
│   │   │   ├── monitoring_service.py # Service monitoring
│   │   │   └── cache_service.py      # Service cache Redis
│   │   │
│   │   ├── tasks/                    # Tâches Celery
│   │   │   ├── celery_app.py         # Configuration Celery
│   │   │   └── message_tasks.py      # Tâches d'envoi
│   │   │
│   │   ├── schemas/                  # Schémas Pydantic
│   │   │   ├── user.py
│   │   │   ├── contact.py
│   │   │   ├── category.py
│   │   │   ├── campaign.py
│   │   │   └── message.py
│   │   │
│   │   └── utils/                    # Utilitaires
│   │       ├── security.py           # JWT, hashing
│   │       ├── validators.py         # Validateurs custom
│   │       └── constants.py          # Constantes
│   │
│   ├── tests/                        # Tests unitaires
│   ├── requirements.txt              # Dépendances Python
│   ├── .env                          # Variables d'environnement
│   ├── .env.example                  # Template .env
│   ├── Procfile                      # Configuration Render
│   └── start.sh                      # Script de démarrage
│
├── frontend/                         # Application Next.js
│   ├── src/
│   │   ├── app/                      # Pages (App Router)
│   │   │   ├── layout.tsx            # Layout principal
│   │   │   ├── page.tsx              # Page d'accueil
│   │   │   ├── login/                # Page de connexion
│   │   │   ├── dashboard/            # Dashboard principal
│   │   │   ├── contacts/             # Gestion contacts
│   │   │   ├── categories/           # Gestion catégories
│   │   │   └── campaigns/            # Gestion campagnes
│   │   │
│   │   ├── components/               # Composants React
│   │   │   ├── ui/                   # Composants de base
│   │   │   ├── layout/               # Layout components
│   │   │   ├── contacts/             # Composants contacts
│   │   │   ├── campaigns/            # Composants campagnes
│   │   │   └── monitoring/           # Composants monitoring
│   │   │
│   │   ├── hooks/                    # Hooks personnalisés
│   │   │   ├── useAuth.ts            # Hook authentification
│   │   │   ├── useContacts.ts        # Hook contacts
│   │   │   ├── useCategories.ts      # Hook catégories
│   │   │   ├── useCampaigns.ts       # Hook campagnes
│   │   │   └── useStats.ts           # Hook statistiques
│   │   │
│   │   ├── lib/                      # Utilitaires
│   │   │   ├── api.ts                # Client API Axios
│   │   │   ├── utils.ts              # Fonctions helper
│   │   │   └── query-client.ts       # Config TanStack Query
│   │   │
│   │   └── types/                    # Types TypeScript
│   │
│   ├── package.json                  # Dépendances Node.js
│   ├── next.config.ts                # Configuration Next.js
│   ├── tailwind.config.ts            # Configuration Tailwind
│   └── .env.local                    # Variables d'environnement
│
├── database/                         # Scripts SQL
│   ├── schema.sql                    # Schéma de base de données
│   ├── rls_policies.sql              # Politiques RLS Supabase
│   ├── migrations/                   # Migrations SQL
│   └── seed_admin.sql                # Données initiales
│
└── docs/                             # Documentation
    ├── DOCUMENTATION_PROJET.md
    ├── GUIDE_CONFIGURATION_WASSENGER_2025.md
    └── audit/                        # Rapports d'audit
```

---

## 🗄️ Base de Données

### Schéma des Tables

```sql
-- Table users (Super Admin et Admin)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(50),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table contacts
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    full_number VARCHAR(25) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    whatsapp_verified BOOLEAN DEFAULT NULL,
    verified_at TIMESTAMP DEFAULT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table category_contacts (many-to-many)
CREATE TABLE category_contacts (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, contact_id)
);

-- Table campaigns
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    message_1 TEXT NOT NULL,
    message_2 TEXT,
    template_name VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft',
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Table campaign_categories (many-to-many)
CREATE TABLE campaign_categories (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE(campaign_id, category_id)
);

-- Table messages (tracking individuel)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    message_type VARCHAR(20) CHECK (message_type IN ('message_1', 'message_2')),
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    whatsapp_message_id VARCHAR(255),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table interactions (webhooks reçus)
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES messages(id),
    interaction_type VARCHAR(50),
    content TEXT,
    whatsapp_message_id VARCHAR(255),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Diagramme Entité-Relation

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
│   users     │     │  category_contacts  │     │  contacts   │
├─────────────┤     ├─────────────────────┤     ├─────────────┤
│ id (PK)     │     │ id (PK)             │     │ id (PK)     │
│ email       │     │ category_id (FK)    │────▶│ full_number │
│ password    │     │ contact_id (FK)     │     │ first_name  │
│ role        │     └─────────────────────┘     │ last_name   │
│ is_active   │              │                  │ whatsapp_   │
└─────────────┘              │                  │   verified  │
      │                      │                  └─────────────┘
      │                      ▼                        │
      │              ┌─────────────┐                  │
      │              │ categories  │                  │
      │              ├─────────────┤                  │
      └─────────────▶│ id (PK)     │                  │
                     │ name        │                  │
                     │ color       │                  │
                     │ created_by  │                  │
                     └─────────────┘                  │
                            │                        │
                            ▼                        │
                     ┌─────────────────────┐         │
                     │ campaign_categories │         │
                     ├─────────────────────┤         │
                     │ campaign_id (FK)    │         │
                     │ category_id (FK)    │         │
                     └─────────────────────┘         │
                            │                        │
                            ▼                        │
                     ┌─────────────┐                 │
                     │  campaigns  │                 │
                     ├─────────────┤                 │
                     │ id (PK)     │                 │
                     │ name        │                 │
                     │ message_1   │                 │
                     │ message_2   │                 │
                     │ status      │                 │
                     └─────────────┘                 │
                            │                        │
                            ▼                        │
                     ┌─────────────┐                 │
                     │  messages   │◀────────────────┘
                     ├─────────────┤
                     │ id (PK)     │
                     │ campaign_id │
                     │ contact_id  │
                     │ message_type│
                     │ content     │
                     │ status      │
                     └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │interactions │
                     ├─────────────┤
                     │ id (PK)     │
                     │ campaign_id │
                     │ contact_id  │
                     │ message_id  │
                     │ type        │
                     │ content     │
                     └─────────────┘
```

---

## 🔧 Backend - API FastAPI

### Endpoints Principaux

#### Authentification (`/api/auth`)
```
POST /api/auth/login          # Connexion (retourne JWT)
POST /api/auth/refresh        # Rafraîchir le token
GET  /api/auth/me             # Profil utilisateur actuel
```

#### Contacts (`/api/contacts`)
```
GET    /api/contacts          # Liste paginée des contacts
POST   /api/contacts          # Créer un contact
GET    /api/contacts/{id}     # Détails d'un contact
PUT    /api/contacts/{id}     # Modifier un contact
DELETE /api/contacts/{id}     # Supprimer un contact
POST   /api/contacts/import   # Import CSV en masse
```

#### Catégories (`/api/categories`)
```
GET    /api/categories                    # Liste des catégories
POST   /api/categories                    # Créer une catégorie
GET    /api/categories/{id}               # Détails d'une catégorie
PUT    /api/categories/{id}               # Modifier une catégorie
DELETE /api/categories/{id}               # Supprimer une catégorie
POST   /api/categories/{id}/contacts      # Ajouter des contacts
DELETE /api/categories/{id}/contacts/{cid}# Retirer un contact
```

#### Campagnes (`/api/campaigns`)
```
GET    /api/campaigns                 # Liste des campagnes
POST   /api/campaigns                 # Créer une campagne
GET    /api/campaigns/{id}            # Détails d'une campagne
PUT    /api/campaigns/{id}            # Modifier une campagne
DELETE /api/campaigns/{id}            # Supprimer une campagne
POST   /api/campaigns/{id}/send       # Lancer l'envoi
POST   /api/campaigns/{id}/stop       # Arrêter l'envoi
POST   /api/campaigns/{id}/retry      # Réessayer les échecs
POST   /api/campaigns/{id}/relaunch   # Relancer la campagne
GET    /api/campaigns/{id}/stats      # Statistiques détaillées
```

#### Vérification WhatsApp (`/api/verify`)
```
POST /api/verify/whatsapp/{contact_id}    # Vérifier un contact
POST /api/verify/whatsapp/bulk            # Vérification en masse
GET  /api/verify/whatsapp/status/{task_id}# Statut de vérification
```

#### Monitoring (`/api/monitoring`)
```
GET /api/monitoring/stats     # Statistiques quotidiennes
GET /api/monitoring/quota     # Quota restant
```

#### Webhooks (`/api/webhooks`)
```
POST /api/webhooks/wassenger  # Réception webhooks Wassenger
```

---

## 💻 Frontend - Next.js

### Pages Principales

| Route | Description |
|-------|-------------|
| `/login` | Page de connexion |
| `/dashboard` | Tableau de bord principal |
| `/dashboard/monitoring` | Monitoring des quotas |
| `/contacts` | Liste des contacts |
| `/contacts/import` | Import CSV |
| `/categories` | Liste des catégories |
| `/categories/[id]` | Détails d'une catégorie |
| `/campaigns` | Liste des campagnes |
| `/campaigns/new` | Créer une campagne |
| `/campaigns/[id]` | Détails d'une campagne |

### Hooks Personnalisés

```typescript
// useAuth.ts - Gestion de l'authentification
const { user, login, logout, isLoading } = useAuth();

// useContacts.ts - Gestion des contacts
const { contacts, createContact, updateContact, deleteContact } = useContacts();

// useCategories.ts - Gestion des catégories
const { categories, createCategory, addContactsToCategory } = useCategories();

// useCampaigns.ts - Gestion des campagnes
const { campaigns, createCampaign, sendCampaign, stopCampaign } = useCampaigns();

// useStats.ts - Statistiques
const { stats, isLoading } = useStats(campaignId);
```

---

## 📨 Système d'Envoi de Messages


### Configuration Anti-Ban WhatsApp

```python
# Configuration dans message_tasks.py

# Délai entre chaque message (5 secondes)
WASSENGER_RATE_LIMIT_SECONDS = 5

# Taille des lots (50 messages par lot)
BATCH_SIZE = 50

# Pause entre les lots (60 secondes)
BATCH_PAUSE_SECONDS = 60

# Délai avant Message 2 si pas de réponse (24 heures)
MESSAGE_2_DELAY_SECONDS = 24 * 60 * 60  # 86400 secondes
```

### Temps d'Envoi Estimés

| Nombre de Messages | Temps Estimé |
|-------------------|--------------|
| 100 messages | ~8 minutes |
| 500 messages | ~42 minutes |
| 1000 messages | ~1.5 heures |

### Flux d'Envoi

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FLUX D'ENVOI DE CAMPAGNE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. POST /api/campaigns/{id}/send                                    │
│     └── Vérifie le quota disponible                                  │
│     └── Crée les messages en BDD (status: pending)                   │
│     └── Lance la tâche Celery send_campaign_messages                 │
│                                                                      │
│  2. Tâche Celery: send_campaign_messages                             │
│     └── Récupère tous les messages pending                           │
│     └── Pour chaque message, programme send_single_message           │
│         avec un délai calculé (rate limit + pause entre lots)        │
│                                                                      │
│  3. Tâche Celery: send_single_message                                │
│     └── Acquiert un verrou d'idempotence (évite doublons)            │
│     └── Vérifie que le message n'est pas déjà envoyé                 │
│     └── Vérifie que la campagne est toujours active                  │
│     └── Attend le rate limit (5 secondes)                            │
│     └── Appelle wassenger_service.send_message()                     │
│     └── Met à jour le statut du message                              │
│     └── Libère le verrou d'idempotence                               │
│                                                                      │
│  4. Webhook Wassenger (statut)                                       │
│     └── Reçoit les mises à jour (sent, delivered, read, failed)      │
│     └── Met à jour le statut du message en BDD                       │
│     └── Met à jour les compteurs de la campagne                      │
│                                                                      │
│  5. Webhook Wassenger (réponse)                                      │
│     └── Reçoit les réponses des contacts                             │
│     └── Enregistre l'interaction en BDD                              │
│     └── Si Message 1 récent (24h) et pas de Message 2 envoyé :       │
│         └── Crée le Message 2 en BDD                                 │
│         └── Lance send_single_message immédiatement                  │
│                                                                      │
│  6. Tâche Celery: update_campaign_status                             │
│     └── Vérifie si tous les contacts ont terminé leur cycle          │
│     └── Marque la campagne comme "completed" si terminée             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Tâches Celery

### Configuration Celery

```python
# celery_app.py

from celery import Celery

celery_app = Celery(
    "chatbot_whatsapp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max par tâche
    worker_prefetch_multiplier=1,  # Une tâche à la fois
    task_acks_late=True,  # Acknowledge après exécution
)
```

### Tâches Disponibles

| Tâche | Description |
|-------|-------------|
| `send_single_message` | Envoie un message individuel |
| `send_campaign_messages` | Orchestre l'envoi d'une campagne |
| `retry_failed_message` | Réessaie un message échoué |
| `retry_campaign_failed_messages` | Réessaie tous les messages échoués |
| `verify_whatsapp_task` | Vérifie un numéro WhatsApp |
| `bulk_verify_task` | Vérification en masse |
| `update_campaign_status` | Met à jour le statut de la campagne |

### Détail des Tâches

#### send_single_message

```python
@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_single_message",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=60,
    time_limit=90,
)
def send_single_message(
    self,
    message_id: int,
    is_template: bool = True,
    template_name: Optional[str] = None,
    content_sid: Optional[str] = None
) -> dict:
    """
    Envoie un message individuel via Wassenger WhatsApp API.
    
    ROBUSTESSE:
    - Verrou d'idempotence pour éviter les doublons
    - Validation des données avant envoi
    - Vérification du statut de la campagne
    - Gestion des timeouts
    - Protection contre les interruptions
    """
```

#### send_campaign_messages

```python
@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_campaign_messages",
    acks_late=True,
)
def send_campaign_messages(
    self,
    campaign_id: int,
    batch_size: int = None
) -> dict:
    """
    Envoie les messages d'une campagne par lots via Wassenger API.
    
    ANTI-BAN STRATEGY 2025:
    - Délai de 5 secondes entre chaque message
    - Envoi par lots de 50 messages avec pause de 60 secondes
    """
```

---

## 🔌 Intégration Wassenger

### Configuration

```python
# Variables d'environnement requises
WASSENGER_API_KEY=votre_api_key
WASSENGER_DEVICE_ID=votre_device_id
WASSENGER_WEBHOOK_URL=https://votre-backend.com/api/webhooks/wassenger
```

### Service Wassenger

```python
# wassenger_service.py

class WassengerService:
    """
    Service pour l'intégration avec Wassenger API 2025.
    
    Fonctionnalités:
    - Envoi de messages texte
    - Vérification d'existence WhatsApp
    - Parsing des webhooks
    - Gestion des erreurs avec retry automatique
    """
    
    BASE_URL = "https://api.wassenger.com/v1"
    
    async def send_message(self, phone: str, text: str) -> WassengerResponse:
        """Envoie un message WhatsApp"""
        
    async def check_whatsapp_exists(self, phone: str, max_retries: int = 4) -> WhatsAppExistsResponse:
        """Vérifie si un numéro est sur WhatsApp"""
        
    def parse_webhook_payload(self, payload: Dict) -> List[WassengerWebhookInteraction]:
        """Parse les webhooks Wassenger"""
```

### Gestion des Erreurs

```python
# Messages d'erreur en français
WASSENGER_ERROR_MESSAGES = {
    "device_not_connected": "L'appareil WhatsApp doit être reconnecté...",
    "invalid_phone_number": "Le format du numéro est incorrect...",
    "rate_limit_exceeded": "Limite de débit atteinte...",
    "session_expired": "La session WhatsApp a expiré...",
    "message_too_long": "Le message dépasse 4096 caractères...",
    "unauthorized": "Erreur d'authentification...",
    "server_error": "Erreur temporaire du serveur...",
}
```

### Retry Automatique

```python
# Configuration des retries pour check_whatsapp_exists
# - 4 tentatives par défaut
# - Délais adaptés selon le type d'erreur:
#   * 502/504 HTML (proxy): 15 secondes
#   * 503 device_not_connected: 20 secondes
#   * Autres 5xx: 10 secondes
# - Timeout de 90 secondes par requête
```

---

## 📡 Webhooks

### Endpoint Wassenger

```python
@router.post("/wassenger", status_code=status.HTTP_200_OK)
async def receive_wassenger_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_supabase_db),
) -> Dict[str, str]:
    """
    Endpoint de réception des webhooks Wassenger 2025.
    
    Événements gérés:
    - message:in:new : Message entrant (réponse)
    - message:out:new : Message sortant créé
    - message:update : Mise à jour de statut
    - message:reaction : Réaction (emoji)
    - message:out:ack : Accusé de réception
    - message:out:failed : Échec d'envoi
    """
```

### Types d'Événements

| Événement | Description | Action |
|-----------|-------------|--------|
| `message:in:new` | Réponse d'un contact | Enregistre l'interaction, envoie Message 2 si applicable |
| `message:out:new` | Message créé | Log uniquement |
| `message:update` | Statut mis à jour | Met à jour le statut du message |
| `message:out:ack` | Accusé de réception | Met à jour delivered/read |
| `message:out:failed` | Échec d'envoi | Marque le message comme failed |
| `message:reaction` | Réaction emoji | Enregistre l'interaction |

---

## ⚙️ Configuration et Déploiement

### Variables d'Environnement Backend

```bash
# .env

# Environnement
ENVIRONMENT=production
DEBUG=false

# API
API_HOST=0.0.0.0
API_PORT=8000

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres

# Wassenger
WASSENGER_API_KEY=votre_api_key
WASSENGER_DEVICE_ID=votre_device_id
WASSENGER_WEBHOOK_URL=https://votre-backend.com/api/webhooks/wassenger

# Redis
REDIS_URL=redis://default:xxx@xxx.upstash.io:6379

# JWT
SECRET_KEY=votre_secret_key_tres_long_et_securise
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
ALLOWED_ORIGINS=https://votre-frontend.netlify.app

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
WHATSAPP_RATE_LIMIT_PER_MINUTE=25

# Retry
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY_SECONDS=60
```

### Variables d'Environnement Frontend

```bash
# .env.local

NEXT_PUBLIC_API_URL=https://votre-backend.onrender.com/api
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Déploiement Render (Backend)

```yaml
# render.yaml

services:
  - type: web
    name: chatbot-whatsapp-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: ./start.sh
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### Déploiement Netlify (Frontend)

```toml
# netlify.toml

[build]
  command = "npm run build"
  publish = ".next"

[[redirects]]
  from = "/api/*"
  to = "https://votre-backend.onrender.com/api/:splat"
  status = 200
  force = true
```

---

## 🚀 Guide d'Installation

### Prérequis

- Python 3.11+
- Node.js 18+
- Redis (local ou Upstash)
- Compte Supabase
- Compte Wassenger avec appareil WhatsApp connecté

### Installation Backend

```bash
# 1. Cloner le projet
git clone https://github.com/votre-repo/chatbot-whatsapp.git
cd chatbot-whatsapp/backend

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# 5. Lancer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Lancer Celery (dans un autre terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

### Installation Frontend

```bash
# 1. Aller dans le dossier frontend
cd ../frontend

# 2. Installer les dépendances
npm install

# 3. Configurer les variables d'environnement
cp .env.example .env.local
# Éditer .env.local avec vos valeurs

# 4. Lancer le serveur de développement
npm run dev
```

### Configuration Supabase

1. Créer un projet sur [supabase.com](https://supabase.com)
2. Exécuter le script `database/schema.sql` dans l'éditeur SQL
3. Exécuter le script `database/rls_policies.sql` pour les politiques de sécurité
4. Exécuter le script `database/seed_admin.sql` pour créer l'admin initial
5. Récupérer les clés API dans Settings > API

### Configuration Wassenger

1. Créer un compte sur [wassenger.com](https://wassenger.com)
2. Ajouter un appareil WhatsApp (scanner le QR code)
3. Récupérer l'API Key dans Settings > API Keys
4. Récupérer le Device ID dans Devices
5. Configurer le webhook vers `https://votre-backend.com/api/webhooks/wassenger`

---

## 📊 Monitoring et Quotas

### Limite Quotidienne

- **1000 messages par jour** (configurable)
- Compteur réinitialisé à minuit UTC
- Vérification avant chaque envoi

### Statistiques Disponibles

```json
{
  "daily_stats": {
    "messages_sent": 150,
    "messages_delivered": 145,
    "messages_read": 120,
    "messages_failed": 5,
    "interactions": 30,
    "quota_remaining": 850
  }
}
```

---

## 🔒 Sécurité

### Authentification JWT

- Tokens d'accès valides 24 heures
- Tokens de rafraîchissement valides 7 jours
- Hachage bcrypt pour les mots de passe

### Rôles Utilisateurs

| Rôle | Permissions |
|------|-------------|
| `super_admin` | Toutes les permissions + gestion des utilisateurs |
| `admin` | Gestion des contacts, catégories, campagnes |

### Rate Limiting

- 100 requêtes/minute par IP (API générale)
- 25 requêtes/minute pour les envois WhatsApp

---

## 🧪 Tests

### Backend

```bash
# Lancer tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ -v --cov=app --cov-report=html

# Tests property-based
pytest tests/test_*_properties.py -v
```

### Frontend

```bash
# Lancer tous les tests
npm run test

# Mode watch
npm run test:watch
```

---

## 📝 Changelog

### Version 1.0.0 (Décembre 2025)

- ✅ Migration complète vers Wassenger API
- ✅ Système Message 1 / Message 2 avec logique 24h
- ✅ Vérification WhatsApp automatique
- ✅ Retry automatique avec backoff exponentiel
- ✅ Monitoring des quotas en temps réel
- ✅ Cache Redis pour les statistiques
- ✅ Tests property-based complets

---

## 🎨 Design UI/UX

### Palette de Couleurs

#### Couleur Principale - Émeraude

| Nom | Code Hex | HSL | Utilisation |
|-----|----------|-----|-------------|
| Emerald 50 | `#D1FAE5` | 160 84% 91% | Badges succès, fonds légers |
| Emerald 100 | `#A7F3D0` | 160 84% 82% | Hover léger |
| Emerald 200 | `#6EE7B7` | 160 84% 67% | Accents secondaires |
| Emerald 300 | `#34D399` | 160 84% 52% | Éléments interactifs |
| **Emerald 400** | `#10B981` | 160 84% 39% | **Couleur principale** |
| Emerald 500 | `#059669` | 160 84% 31% | Hover boutons |
| Emerald 600 | `#047857` | 160 84% 25% | États actifs |
| Emerald 700 | `#065F46` | 160 84% 19% | Texte sur fond clair |
| Emerald 800 | `#064E3B` | 160 84% 15% | Accents foncés |
| Emerald 900 | `#022C22` | 160 84% 9% | Texte très foncé |

#### Couleurs de Statut

| Statut | Code Hex | Utilisation |
|--------|----------|-------------|
| Success | `#10B981` | Messages envoyés, validations |
| Error | `#EF4444` | Erreurs, suppressions |
| Warning | `#F59E0B` | Alertes, en attente |
| Pending | `#F59E0B` | Messages en cours |

#### Couleurs de Texte

| Type | Code Hex | Utilisation |
|------|----------|-------------|
| Primary | `#111827` | Titres, texte principal |
| Secondary | `#6B7280` | Descriptions, labels |
| Muted | `#9CA3AF` | Texte désactivé, placeholders |

#### Couleurs de Surface

| Type | Code Hex | Utilisation |
|------|----------|-------------|
| Background | `#F9FAFB` | Fond de page |
| Card | `#FFFFFF` | Cartes, conteneurs |
| Hover | `#F3F4F6` | États hover |
| Border | `#E5E7EB` | Bordures, séparateurs |

#### Sidebar

| Type | Code Hex | Utilisation |
|------|----------|-------------|
| Background | `#1F2937` | Fond sidebar |
| Text | `#9CA3AF` | Liens inactifs |
| Text Active | `#10B981` | Lien actif (émeraude) |
| Hover | `rgba(255,255,255,0.05)` | Hover sur liens |

### Typographie

#### Police Principale

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

**Inter** est une police sans-serif moderne, optimisée pour les interfaces utilisateur avec une excellente lisibilité sur écran.

#### Tailles de Texte

| Classe | Taille | Utilisation |
|--------|--------|-------------|
| `text-xs` | 12px | Labels, badges |
| `text-sm` | 14px | Texte secondaire, descriptions |
| `text-base` | 16px | Texte principal |
| `text-lg` | 18px | Sous-titres |
| `text-xl` | 20px | Titres de section |
| `text-2xl` | 24px | Titres de page |
| `text-3xl` | 30px | Titres principaux |

#### Poids de Police

| Classe | Poids | Utilisation |
|--------|-------|-------------|
| `font-normal` | 400 | Texte courant |
| `font-medium` | 500 | Labels, boutons |
| `font-semibold` | 600 | Sous-titres |
| `font-bold` | 700 | Titres |

### Composants UI

#### Boutons

```typescript
// Variantes disponibles
const buttonVariants = {
  default: "bg-emerald-500 text-white hover:bg-emerald-500/90",
  destructive: "bg-[#EF4444] text-white hover:bg-[#EF4444]/90",
  outline: "border border-[#E5E7EB] bg-white text-[#374151] hover:bg-[#F9FAFB]",
  secondary: "bg-[#F3F4F6] text-[#374151] hover:bg-[#E5E7EB]",
  ghost: "text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827]",
  link: "text-emerald-500 underline-offset-4 hover:underline",
  success: "bg-emerald-500 text-white hover:bg-emerald-500/90",
};

// Tailles disponibles
const buttonSizes = {
  default: "h-10 px-4 py-2",
  sm: "h-9 rounded-lg px-3",
  lg: "h-12 rounded-lg px-8",
  icon: "h-10 w-10",
};
```

#### Cartes

```css
/* Style de base */
.card {
  background: #FFFFFF;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Hover */
.card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

#### Badges de Statut

```css
.badge-success { background: #D1FAE5; color: #059669; }
.badge-error { background: #FEE2E2; color: #DC2626; }
.badge-warning { background: #FEF3C7; color: #D97706; }
.badge-pending { background: #FEF3C7; color: #D97706; }
```

#### Inputs

```css
/* Style de base */
input {
  height: 48px;
  padding-left: 40px; /* Pour l'icône */
  border-radius: 8px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
}

/* Focus */
input:focus {
  border-color: #10B981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

/* Erreur */
input.error {
  border-color: #EF4444;
}
```

### Structure du Dashboard

#### Layout Principal

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LAYOUT DASHBOARD                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌────────────────────────────────────────────┐   │
│  │              │  │                                            │   │
│  │   SIDEBAR    │  │              CONTENU PRINCIPAL             │   │
│  │   (264px)    │  │                                            │   │
│  │              │  │  ┌──────────────────────────────────────┐  │   │
│  │  - Logo      │  │  │         HEADER (Titre + Actions)     │  │   │
│  │  - Nav       │  │  └──────────────────────────────────────┘  │   │
│  │  - Profil    │  │                                            │   │
│  │  - Logout    │  │  ┌──────────────────────────────────────┐  │   │
│  │              │  │  │                                      │  │   │
│  │              │  │  │           ZONE DE CONTENU            │  │   │
│  │              │  │  │                                      │  │   │
│  │              │  │  │                                      │  │   │
│  │              │  │  └──────────────────────────────────────┘  │   │
│  │              │  │                                            │   │
│  └──────────────┘  └────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Sidebar - Navigation

| Icône | Label | Route | Rôle |
|-------|-------|-------|------|
| 📊 | Dashboard | `/dashboard` | Tous |
| 📁 | Catégories | `/categories` | Tous |
| 👥 | Contacts | `/contacts` | Tous |
| 📤 | Campagnes | `/campaigns` | Tous |
| 💬 | Messages | `/messages` | Tous |
| 📈 | Statistiques | `/statistics` | Tous |
| 🔔 | Monitoring | `/dashboard/monitoring` | Tous |
| 👤 | Utilisateurs | `/admin-users` | Super Admin |

#### Dashboard - Sections

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PAGE DASHBOARD                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Bienvenue, [Nom] 👋                    [+ Nouvelle campagne]  │ │
│  │  Voici un aperçu de votre activité WhatsApp                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ Messages    │ │ Taux de     │ │ Contacts    │ │ Coût        │   │
│  │ envoyés     │ │ réussite    │ │             │ │ estimé      │   │
│  │    150      │ │   95.2%     │ │    1,234    │ │   7,50 €    │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│                                                                      │
│  ┌─────────────────────────┐ ┌─────────────────────────┐           │
│  │ Catégories              │ │ Campagnes               │           │
│  │    12                   │ │    8                    │           │
│  └─────────────────────────┘ └─────────────────────────┘           │
│                                                                      │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐   │
│  │                             │ │                             │   │
│  │  📈 Évolution des envois   │ │  🥧 Répartition des statuts │   │
│  │     (7 derniers jours)     │ │                             │   │
│  │                             │ │                             │   │
│  │     [Graphique ligne]      │ │     [Graphique camembert]   │   │
│  │                             │ │                             │   │
│  └─────────────────────────────┘ └─────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  📬 Messages récents                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ +229 97 XX XX XX │ Message 1 │ ✅ Envoyé │ Il y a 5 min  │  │ │
│  │  │ +229 96 XX XX XX │ Message 2 │ 📖 Lu     │ Il y a 10 min │  │ │
│  │  │ +229 95 XX XX XX │ Message 1 │ ❌ Échec  │ Il y a 15 min │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│                    [Voir les statistiques détaillées]               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Page de Connexion

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PAGE LOGIN                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐   │
│  │                             │ │                             │   │
│  │  FORMULAIRE DE CONNEXION    │ │  DÉCORATION (Desktop only)  │   │
│  │                             │ │                             │   │
│  │  Fond: Dégradé bleu clair   │ │  Fond: Dégradé émeraude     │   │
│  │  #e0f2fe → #bae6fd          │ │  #a7f3d0 → #6ee7b7 → #5eead4│   │
│  │                             │ │                             │   │
│  │  ┌───────────────────────┐  │ │     ○ ○                     │   │
│  │  │                       │  │ │        ○                    │   │
│  │  │   [Logo Émeraude]     │  │ │           ○                 │   │
│  │  │   WhatsApp Chatbot    │  │ │                             │   │
│  │  │                       │  │ │     [Logo WhatsApp]         │   │
│  │  │   ┌─────────────────┐ │  │ │                             │   │
│  │  │   │ 📧 Email        │ │  │ │   "Gérez vos campagnes      │   │
│  │  │   └─────────────────┘ │  │ │    WhatsApp"                │   │
│  │  │                       │  │ │                             │   │
│  │  │   ┌─────────────────┐ │  │ │   "Envoyez des messages     │   │
│  │  │   │ 🔒 Mot de passe │ │  │ │    personnalisés..."        │   │
│  │  │   └─────────────────┘ │  │ │                             │   │
│  │  │                       │  │ │        ○                    │   │
│  │  │   [Se connecter]      │  │ │     ○                       │   │
│  │  │                       │  │ │                             │   │
│  │  └───────────────────────┘  │ │                             │   │
│  │                             │ │                             │   │
│  └─────────────────────────────┘ └─────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Dégradés pour Catégories

```css
/* 6 dégradés prédéfinis pour les cartes de catégories */
.gradient-1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); } /* Violet */
.gradient-2 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); } /* Rose */
.gradient-3 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); } /* Bleu cyan */
.gradient-4 { background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%); } /* Rose-bleu */
.gradient-5 { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); } /* Vert-bleu */
.gradient-6 { background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); } /* Bleu foncé */
```

### Responsive Design

#### Breakpoints

| Nom | Taille | Utilisation |
|-----|--------|-------------|
| `xs` | 375px | Petits mobiles |
| `sm` | 640px | Mobiles |
| `md` | 768px | Tablettes |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Grand desktop |
| `2xl` | 1536px | Très grand écran |

#### Comportement Mobile

- **Sidebar** : Masquée par défaut, accessible via menu hamburger
- **Cartes stats** : Empilées verticalement (1 colonne)
- **Graphiques** : Pleine largeur
- **Boutons** : Hauteur minimale de 44px pour le touch

### Animations

```css
/* Slide in depuis la gauche (sidebar mobile) */
@keyframes slideInFromLeft {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

/* Fade in */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Accordion (Radix UI) */
@keyframes accordion-down {
  from { height: 0; }
  to { height: var(--radix-accordion-content-height); }
}
```

### Accessibilité

- **Focus visible** : Ring émeraude sur tous les éléments interactifs
- **Contraste** : Ratio minimum 4.5:1 pour le texte
- **Touch targets** : Minimum 44x44px sur mobile
- **Labels** : Tous les inputs ont des labels associés
- **ARIA** : Attributs aria-label sur les boutons icônes

---

## 📞 Support

Pour toute question ou problème :
- Consulter la documentation dans `/docs`
- Vérifier les logs Celery pour les erreurs d'envoi
- Vérifier le dashboard Wassenger pour l'état de l'appareil

---

*Documentation générée le 30 décembre 2025*

# 📱 Documentation Technique du Projet
## Plateforme de Gestion de Campagnes WhatsApp

**Version** : 1.0.0  
**Date de création** : Décembre 2025  
**Dernière mise à jour** : 27 décembre 2025

---

## 📋 Table des Matières

1. [Vue d'Ensemble du Projet](#1-vue-densemble-du-projet)
2. [Architecture Technique](#2-architecture-technique)
3. [Stack Technologique](#3-stack-technologique)
4. [Structure du Projet](#4-structure-du-projet)
5. [Backend - API FastAPI](#5-backend---api-fastapi)
6. [Frontend - Application Next.js](#6-frontend---application-nextjs)
7. [Base de Données](#7-base-de-données)
8. [Intégration WhatsApp (Wassenger)](#8-intégration-whatsapp-wassenger)
9. [Système de Tâches Asynchrones](#9-système-de-tâches-asynchrones)
10. [Monitoring et Limites](#10-monitoring-et-limites)
11. [Sécurité](#11-sécurité)
12. [Tests](#12-tests)
13. [Déploiement](#13-déploiement)
14. [État du Projet](#14-état-du-projet)

---

## 1. Vue d'Ensemble du Projet

### 1.1 Objectif

Cette plateforme est un **système complet de gestion de campagnes WhatsApp** permettant :

- ✅ L'envoi automatisé de messages WhatsApp à grande échelle
- ✅ La gestion de contacts organisés par catégories
- ✅ La création et le suivi de campagnes marketing
- ✅ Le monitoring en temps réel avec respect des limites d'envoi
- ✅ La vérification des numéros WhatsApp
- ✅ Le suivi des interactions (réponses, lectures, livraisons)

### 1.2 Fonctionnalités Principales

| Fonctionnalité | Description |
|----------------|-------------|
| **Authentification** | JWT avec rôles (Super Admin / Admin) |
| **Gestion des Contacts** | Import CSV, vérification WhatsApp, organisation par catégories |
| **Campagnes** | Création, envoi massif, suivi en temps réel |
| **Messages** | Message 1 (initial) + Message 2 (suivi après interaction) |
| **Monitoring** | Limite de 1000 messages/jour, alertes visuelles |
| **Webhooks** | Réception des statuts WhatsApp (envoyé, livré, lu) |
| **Statistiques** | Dashboard avec métriques en temps réel |

### 1.3 Flux de Données Principal

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│  API REST   │────▶│   Celery    │────▶│  Wassenger  │
│  (Next.js)  │     │  (FastAPI)  │     │   (Redis)   │     │    API      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       │                   ▼                   │                   │
       │            ┌─────────────┐            │                   │
       │            │  Supabase   │◀───────────┘                   │
       │            │ (PostgreSQL)│                                │
       │            └─────────────┘                                │
       │                   ▲                                       │
       │                   │                                       │
       └───────────────────┴───────────────────────────────────────┘
                        Webhooks (statuts messages)
```

---

## 2. Architecture Technique

### 2.1 Architecture Globale

Le projet suit une architecture **microservices légère** avec séparation claire des responsabilités :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           COUCHE PRÉSENTATION                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Frontend Next.js 16                           │   │
│  │  • React 19 + TypeScript                                         │   │
│  │  • TanStack Query (cache & état serveur)                         │   │
│  │  • Tailwind CSS + Radix UI                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            COUCHE API                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Backend FastAPI                               │   │
│  │  • Routers : auth, contacts, categories, campaigns, messages     │   │
│  │  • Services : wassenger, monitoring, message                     │   │
│  │  • Middleware : CORS, JWT, Rate Limiting                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         COUCHE MÉTIER                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐                    │
│  │    Celery Workers    │  │   Monitoring Service │                    │
│  │  • Envoi messages    │  │  • Compteurs Redis   │                    │
│  │  • Retries auto      │  │  • Alertes           │                    │
│  │  • Rate limiting     │  │  • Sync Supabase     │                    │
│  └──────────────────────┘  └──────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         COUCHE DONNÉES                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐                    │
│  │      Supabase        │  │        Redis         │                    │
│  │  • PostgreSQL        │  │  • Message Broker    │                    │
│  │  • Auth (optionnel)  │  │  • Cache compteurs   │                    │
│  │  • RLS Policies      │  │  • Rate limiting     │                    │
│  └──────────────────────┘  └──────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SERVICES EXTERNES                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Wassenger API                                 │   │
│  │  • Envoi messages WhatsApp                                       │   │
│  │  • Vérification numéros                                          │   │
│  │  • Webhooks statuts                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Principes Architecturaux

1. **Séparation des Responsabilités** : Chaque couche a un rôle défini
2. **Asynchronisme** : Celery pour les tâches longues (envoi massif)
3. **Résilience** : Retries automatiques, circuit breakers, idempotence
4. **Scalabilité** : Workers Celery parallélisables, Redis distribué
5. **Observabilité** : Logging structuré, monitoring temps réel

---

## 3. Stack Technologique

### 3.1 Backend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.11+ | Langage principal |
| **FastAPI** | 0.109+ | Framework API REST |
| **Celery** | 5.3+ | Tâches asynchrones |
| **Redis** | 5.0+ | Message broker + cache |
| **Supabase** | 2.3+ | Client PostgreSQL |
| **Pydantic** | 2.5+ | Validation des données |
| **httpx** | 0.26+ | Client HTTP async |
| **Hypothesis** | 6.92+ | Tests property-based |

### 3.2 Frontend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Next.js** | 16.1+ | Framework React |
| **React** | 19.2 | Bibliothèque UI |
| **TypeScript** | 5.9+ | Typage statique |
| **TanStack Query** | 5.90+ | Gestion état serveur |
| **Tailwind CSS** | 4.0 | Styles utilitaires |
| **Radix UI** | - | Composants accessibles |
| **Axios** | 1.13+ | Client HTTP |
| **Zod** | 4.1+ | Validation schémas |
| **Vitest** | 4.0+ | Tests unitaires |
| **fast-check** | 4.4+ | Tests property-based |

### 3.3 Infrastructure

| Service | Rôle |
|---------|------|
| **Supabase** | Base de données PostgreSQL hébergée |
| **Redis** | Cache et message broker |
| **Wassenger** | API WhatsApp Business |

---

## 4. Structure du Projet

### 4.1 Vue d'Ensemble

```
projet/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── config.py          # Configuration (variables d'environnement)
│   │   ├── main.py            # Point d'entrée FastAPI
│   │   ├── database.py        # Connexion DB (legacy)
│   │   ├── supabase_client.py # Client Supabase
│   │   ├── models/            # Modèles de données
│   │   ├── schemas/           # Schémas Pydantic
│   │   ├── routers/           # Endpoints API
│   │   ├── services/          # Logique métier
│   │   ├── tasks/             # Tâches Celery
│   │   └── utils/             # Utilitaires
│   ├── tests/                 # Tests backend
│   └── requirements.txt       # Dépendances Python
│
├── frontend/                   # Application Next.js
│   ├── src/
│   │   ├── app/               # Pages (App Router)
│   │   ├── components/        # Composants React
│   │   ├── hooks/             # Hooks personnalisés
│   │   ├── lib/               # Utilitaires
│   │   ├── types/             # Types TypeScript
│   │   └── __tests__/         # Tests frontend
│   └── package.json           # Dépendances Node.js
│
├── database/                   # Scripts SQL
│   ├── schema.sql             # Schéma de base
│   ├── migrations/            # Migrations
│   └── rls_policies.sql       # Politiques de sécurité
│
├── docs/                       # Documentation
│
└── .kiro/                      # Specs Kiro
    ├── specs/                 # Spécifications fonctionnelles
    └── steering/              # Règles de guidage
```


### 4.2 Structure Backend Détaillée

```
backend/app/
├── config.py                   # Variables d'environnement (Pydantic Settings)
├── main.py                     # Application FastAPI, middlewares, routers
├── supabase_client.py          # Client Supabase thread-safe
│
├── routers/                    # Endpoints API REST
│   ├── auth.py                # POST /login, /register, /me
│   ├── contacts.py            # CRUD contacts, import CSV
│   ├── categories.py          # CRUD catégories
│   ├── campaigns.py           # CRUD campagnes, envoi, stats
│   ├── messages.py            # Liste messages, statuts
│   ├── users.py               # Gestion utilisateurs (admin)
│   ├── verify.py              # Vérification WhatsApp
│   ├── monitoring.py          # Stats monitoring temps réel
│   └── webhooks.py            # Réception webhooks Wassenger
│
├── schemas/                    # Schémas Pydantic (validation)
│   ├── auth.py                # LoginRequest, TokenResponse
│   ├── contact.py             # ContactCreate, ContactResponse
│   ├── category.py            # CategoryCreate, CategoryResponse
│   ├── campaign.py            # CampaignCreate, CampaignStats
│   ├── message.py             # MessageResponse
│   └── user.py                # UserCreate, UserResponse
│
├── services/                   # Logique métier
│   ├── wassenger_service.py   # Intégration API Wassenger
│   ├── monitoring_service.py  # Compteurs Redis, alertes
│   ├── message_service.py     # Gestion messages/campagnes
│   └── auth_service.py        # Authentification JWT
│
├── tasks/                      # Tâches Celery asynchrones
│   ├── celery_app.py          # Configuration Celery
│   └── message_tasks.py       # Envoi messages, retries
│
└── utils/                      # Utilitaires
    ├── security.py            # JWT, hashing passwords
    ├── validators.py          # Validateurs personnalisés
    └── constants.py           # Constantes globales
```

### 4.3 Structure Frontend Détaillée

```
frontend/src/
├── app/                        # Pages Next.js (App Router)
│   ├── layout.tsx             # Layout principal
│   ├── page.tsx               # Page d'accueil
│   ├── login/                 # Page de connexion
│   ├── dashboard/             # Dashboard principal
│   │   └── monitoring/        # Page monitoring
│   ├── contacts/              # Gestion contacts
│   │   └── import/            # Import CSV
│   ├── categories/            # Gestion catégories
│   ├── campaigns/             # Gestion campagnes
│   │   ├── new/               # Création campagne
│   │   └── [id]/              # Détail campagne
│   ├── messages/              # Liste messages
│   ├── statistics/            # Statistiques
│   └── admin-users/           # Gestion utilisateurs
│
├── components/                 # Composants React
│   ├── ui/                    # Composants de base (Radix)
│   ├── common/                # Composants partagés
│   ├── layout/                # Navigation, sidebar
│   ├── contacts/              # Composants contacts
│   ├── categories/            # Composants catégories
│   ├── campaigns/             # Composants campagnes
│   ├── monitoring/            # Jauges, alertes
│   └── whatsapp/              # Badges vérification
│
├── hooks/                      # Hooks personnalisés
│   ├── useAuth.ts             # Authentification
│   ├── useContacts.ts         # CRUD contacts
│   ├── useCategories.ts       # CRUD catégories
│   ├── useCampaigns.ts        # CRUD campagnes
│   ├── useMessages.ts         # Liste messages
│   ├── useMonitoring.ts       # Stats monitoring
│   └── useStats.ts            # Statistiques globales
│
├── lib/                        # Utilitaires
│   ├── api.ts                 # Client Axios configuré
│   ├── supabase.ts            # Client Supabase
│   ├── utils.ts               # Fonctions utilitaires
│   └── constants.ts           # Constantes
│
└── types/                      # Types TypeScript
    ├── auth.ts                # User, LoginRequest
    ├── contact.ts             # Contact, ContactFilters
    ├── category.ts            # Category
    ├── campaign.ts            # Campaign, CampaignStats
    ├── message.ts             # Message
    └── monitoring.ts          # MonitoringStats
```

---

## 5. Backend - API FastAPI

### 5.1 Configuration

Le fichier `config.py` centralise toutes les variables d'environnement :

```python
class Settings(BaseSettings):
    # Environnement
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # Wassenger API
    WASSENGER_API_KEY: str
    WASSENGER_DEVICE_ID: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    
    # Rate Limiting
    WHATSAPP_RATE_LIMIT_PER_MINUTE: int = 25
```

### 5.2 Endpoints API

#### Authentification (`/api/auth`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/login` | Connexion utilisateur |
| POST | `/register` | Inscription (admin only) |
| GET | `/me` | Profil utilisateur courant |
| POST | `/refresh` | Rafraîchir le token |

#### Contacts (`/api/contacts`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Liste paginée avec filtres |
| POST | `/` | Créer un contact |
| GET | `/{id}` | Détail d'un contact |
| PUT | `/{id}` | Modifier un contact |
| DELETE | `/{id}` | Supprimer un contact |
| POST | `/import` | Import CSV |

#### Catégories (`/api/categories`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Liste des catégories |
| POST | `/` | Créer une catégorie |
| GET | `/{id}` | Détail avec contacts |
| PUT | `/{id}` | Modifier une catégorie |
| DELETE | `/{id}` | Supprimer une catégorie |

#### Campagnes (`/api/campaigns`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Liste des campagnes |
| POST | `/` | Créer une campagne |
| GET | `/{id}` | Détail d'une campagne |
| POST | `/{id}/send` | Lancer l'envoi |
| POST | `/{id}/stop` | Arrêter l'envoi |
| POST | `/{id}/retry` | Réessayer les échecs |
| POST | `/{id}/relaunch` | Relancer complètement |
| GET | `/{id}/stats` | Statistiques détaillées |
| DELETE | `/{id}` | Supprimer une campagne |

#### Vérification WhatsApp (`/api/verify`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/{contact_id}` | Vérifier un contact |
| POST | `/bulk` | Vérification en masse |
| GET | `/stats` | Stats de vérification |

#### Monitoring (`/api/monitoring`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/stats` | Stats temps réel |
| GET | `/capacity` | Capacité restante |

#### Webhooks (`/api/webhooks`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/wassenger` | Réception webhooks Wassenger |

### 5.3 Services Principaux

#### WassengerService

Gère l'intégration avec l'API Wassenger :

```python
class WassengerService:
    async def send_message(self, phone: str, text: str) -> WassengerResponse
    async def check_whatsapp_exists(self, phone: str) -> WhatsAppExistsResponse
    def parse_webhook_payload(self, payload: dict) -> List[WassengerWebhookInteraction]
```

#### MonitoringService

Gère les compteurs Redis et les alertes :

```python
class MonitoringService:
    def increment_message_counter(self, message_type: str) -> int
    def get_daily_stats(self) -> DailyStats
    def can_send_message(self) -> Tuple[bool, str]
    def get_alert_level(self) -> AlertLevel  # ok, attention, danger, blocked
    def calculate_remaining_capacity(self) -> int
```

---

## 6. Frontend - Application Next.js

### 6.1 Gestion de l'État

Le projet utilise **TanStack Query** pour la gestion de l'état serveur :

```typescript
// Exemple : Hook pour les campagnes
export function useCampaigns(params: CampaignFilters = {}) {
  return useQuery({
    queryKey: campaignKeys.list(params),
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Campaign>>(`/campaigns`);
      return response.data;
    },
  });
}

// Mutation avec invalidation automatique du cache
export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CampaignCreate) => {
      const response = await api.post<Campaign>("/campaigns", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}
```

### 6.2 Client API

Le client Axios est configuré avec :
- Intercepteurs pour le JWT
- Refresh automatique des tokens
- Retries automatiques sur erreurs réseau
- Gestion centralisée des erreurs

```typescript
// Configuration robuste
const MAX_RETRIES = 3;
const REQUEST_TIMEOUT_MS = 30000;

// Intercepteur de requête : ajout du token JWT
api.interceptors.request.use(async (config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur de réponse : retry automatique
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (isRetryableError(error)) {
      // Retry avec backoff exponentiel
    }
    // Refresh token si 401
  }
);
```

### 6.3 Pages Principales

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | Authentification |
| Dashboard | `/dashboard` | Vue d'ensemble |
| Monitoring | `/dashboard/monitoring` | Suivi temps réel |
| Contacts | `/contacts` | Liste des contacts |
| Import | `/contacts/import` | Import CSV |
| Catégories | `/categories` | Gestion catégories |
| Campagnes | `/campaigns` | Liste campagnes |
| Nouvelle Campagne | `/campaigns/new` | Création |
| Détail Campagne | `/campaigns/[id]` | Suivi envoi |
| Messages | `/messages` | Historique |
| Statistiques | `/statistics` | Métriques |
| Utilisateurs | `/admin-users` | Gestion admins |

---

## 7. Base de Données

### 7.1 Schéma Relationnel

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
│   users     │     │  category_contacts  │     │  categories │
├─────────────┤     ├─────────────────────┤     ├─────────────┤
│ id (PK)     │     │ id (PK)             │     │ id (PK)     │
│ email       │     │ category_id (FK)    │────▶│ name        │
│ password    │     │ contact_id (FK)     │     │ color       │
│ role        │     └─────────────────────┘     │ created_by  │
│ is_active   │              │                  └─────────────┘
└─────────────┘              │
       │                     ▼
       │              ┌─────────────┐
       │              │  contacts   │
       │              ├─────────────┤
       │              │ id (PK)     │
       │              │ phone_number│
       │              │ country_code│
       │              │ full_number │
       │              │ first_name  │
       │              │ last_name   │
       │              │ whatsapp_   │
       │              │   verified  │
       │              │ created_by  │
       │              └─────────────┘
       │                     │
       ▼                     ▼
┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
│  campaigns  │     │ campaign_categories │     │  messages   │
├─────────────┤     ├─────────────────────┤     ├─────────────┤
│ id (PK)     │◀────│ campaign_id (FK)    │     │ id (PK)     │
│ name        │     │ category_id (FK)    │     │ campaign_id │
│ message_1   │     └─────────────────────┘     │ contact_id  │
│ message_2   │                                 │ message_type│
│ status      │────────────────────────────────▶│ content     │
│ total_      │                                 │ status      │
│  recipients │                                 │ whatsapp_   │
│ sent_count  │                                 │   message_id│
│ success_    │                                 │ sent_at     │
│   count     │                                 │ delivered_at│
│ failed_count│                                 │ read_at     │
│ created_by  │                                 │ error_msg   │
└─────────────┘                                 └─────────────┘
                                                       │
                                                       ▼
                                                ┌─────────────┐
                                                │interactions │
                                                ├─────────────┤
                                                │ id (PK)     │
                                                │ campaign_id │
                                                │ contact_id  │
                                                │ message_id  │
                                                │ interaction_│
                                                │   type      │
                                                │ content     │
                                                │ received_at │
                                                └─────────────┘
```

### 7.2 Tables Principales

#### `users`
Utilisateurs du système avec rôles `super_admin` ou `admin`.

#### `contacts`
Contacts WhatsApp avec :
- Numéro international (`full_number`)
- Statut de vérification WhatsApp (`whatsapp_verified`)
- Timestamp de vérification (`verified_at`)

#### `categories`
Catégories pour organiser les contacts (relation many-to-many via `category_contacts`).

#### `campaigns`
Campagnes d'envoi avec :
- Deux messages possibles (`message_1`, `message_2`)
- Statuts : `draft`, `sending`, `completed`, `failed`
- Compteurs de suivi

#### `messages`
Messages individuels avec tracking :
- Statuts : `pending`, `sent`, `delivered`, `read`, `failed`
- ID WhatsApp pour le suivi
- Compteur de retries

#### `interactions`
Interactions reçues via webhooks :
- Types : `reply`, `reaction`, `read`, `delivered`


---

## 8. Intégration WhatsApp (Wassenger)

### 8.1 Présentation

Le projet utilise **Wassenger API** pour l'envoi de messages WhatsApp. Cette API permet :
- L'envoi de messages texte
- La vérification de numéros WhatsApp
- La réception de webhooks pour les statuts

### 8.2 Configuration Requise

```env
# Variables d'environnement Wassenger
WASSENGER_API_KEY=votre_api_key
WASSENGER_DEVICE_ID=votre_device_id
WASSENGER_WEBHOOK_URL=https://votre-domaine.com/api/webhooks/wassenger
```

### 8.3 Envoi de Messages

```python
# Service Wassenger
async def send_message(self, phone: str, text: str) -> WassengerResponse:
    """
    Envoie un message WhatsApp via Wassenger API.
    
    Args:
        phone: Numéro au format international (ex: 22890123456)
        text: Contenu du message
    
    Returns:
        WassengerResponse avec success, message_id ou error
    """
    payload = {
        "phone": self.format_phone_number(phone),
        "message": text,
        "device": self.device_id
    }
    response = await client.post(f"{BASE_URL}/messages", json=payload)
```

### 8.4 Vérification de Numéros

```python
async def check_whatsapp_exists(self, phone: str) -> WhatsAppExistsResponse:
    """
    Vérifie si un numéro est enregistré sur WhatsApp.
    
    Returns:
        WhatsAppExistsResponse avec exists=True/False
    """
    response = await client.post(
        f"{BASE_URL}/numbers/exists",
        json={"phone": formatted_phone}
    )
```

### 8.5 Webhooks

Les webhooks Wassenger sont reçus sur `/api/webhooks/wassenger` :

| Événement | Description |
|-----------|-------------|
| `message:in:new` | Message entrant (réponse) |
| `message:out:new` | Message sortant créé |
| `message:update` | Mise à jour de statut |
| `message:out:ack` | Accusé de réception |
| `message:out:failed` | Échec d'envoi |
| `message:reaction` | Réaction à un message |

### 8.6 Stratégie Anti-Ban

Pour éviter les bans WhatsApp, le système respecte :

```python
# Configuration anti-ban
WASSENGER_RATE_LIMIT_SECONDS = 25  # 25s entre chaque message
BATCH_SIZE = 25                     # Lots de 25 messages
BATCH_PAUSE_SECONDS = 300           # 5 min de pause entre lots

# Pour 1000 messages : ~7-8 heures d'envoi
```

---

## 9. Système de Tâches Asynchrones

### 9.1 Architecture Celery

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│   Celery    │
│   (API)     │     │  (Broker)   │     │  (Workers)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Queues    │
                    ├─────────────┤
                    │ • default   │
                    │ • messages  │
                    │ • retry     │
                    │ • verify    │
                    └─────────────┘
```

### 9.2 Tâches Principales

#### `send_single_message`
Envoie un message individuel avec :
- Vérification de la limite quotidienne
- Idempotence (évite les doublons)
- Retries automatiques (max 3)
- Mise à jour des statistiques

#### `send_campaign_messages`
Orchestre l'envoi d'une campagne :
- Découpage en lots de 25 messages
- Pauses de 5 minutes entre lots
- Respect du rate limit (25s/message)

#### Tâches Périodiques (Celery Beat)

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| `sync_monitoring_to_supabase` | 1h | Persiste les compteurs Redis |
| `reset_daily_monitoring` | 00:00 UTC | Reset quotidien |
| `cleanup_expired_locks` | 10 min | Nettoyage verrous |
| `recover_interrupted_campaigns` | 5 min | Reprise après crash |
| `system_health_check` | 2 min | Vérification santé |

### 9.3 Robustesse

Le système intègre plusieurs mécanismes de robustesse :

1. **Idempotence** : Verrous Redis pour éviter les doublons
2. **Retries** : Backoff exponentiel (30s, 60s, 120s)
3. **Timeouts** : Soft limit 60s, hard limit 90s
4. **Recovery** : Reprise automatique des campagnes interrompues
5. **Health Checks** : Surveillance continue du système

---

## 10. Monitoring et Limites

### 10.1 Limite Quotidienne

Le système impose une limite de **1000 messages par jour** pour respecter les bonnes pratiques WhatsApp.

### 10.2 Niveaux d'Alerte

| Niveau | Seuil | Couleur | Action |
|--------|-------|---------|--------|
| `ok` | 0-75% (0-750) | Vert | Normal |
| `attention` | 76-90% (751-900) | Jaune | Avertissement |
| `danger` | 91-100% (901-1000) | Rouge | Critique |
| `blocked` | >100% (>1000) | Gris | Bloqué |

### 10.3 Compteurs Redis

```python
# Clés Redis pour le monitoring
whatsapp:daily:{YYYY-MM-DD}:message_1  # Compteur Message 1
whatsapp:daily:{YYYY-MM-DD}:message_2  # Compteur Message 2
whatsapp:daily:{YYYY-MM-DD}:errors     # Compteur erreurs

# TTL : 48 heures
```

### 10.4 Calcul de Capacité

```python
def calculate_remaining_capacity(self) -> int:
    """
    Formule: floor((1000 - sent) / (1 + interaction_rate))
    
    Prend en compte le taux d'interaction pour estimer
    le nombre de contacts pouvant encore être contactés.
    """
```

### 10.5 Interface de Monitoring

Le dashboard de monitoring affiche :
- Jauge de messages envoyés (avec couleurs d'alerte)
- Compteurs Message 1 / Message 2 / Erreurs
- Capacité restante estimée
- Taux d'erreur (alerte si > 10%)

---

## 11. Sécurité

### 11.1 Authentification JWT

```python
# Configuration JWT
SECRET_KEY: str                        # Clé secrète
ALGORITHM: str = "HS256"               # Algorithme
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7 jours
```

### 11.2 Rôles Utilisateurs

| Rôle | Permissions |
|------|-------------|
| `super_admin` | Toutes les permissions + gestion utilisateurs |
| `admin` | Gestion contacts, catégories, campagnes |

### 11.3 Sécurité API

- **CORS** : Origines autorisées configurables
- **Rate Limiting** : 100 requêtes/minute par défaut
- **Validation** : Pydantic pour toutes les entrées
- **Sanitization** : Nettoyage des chaînes de caractères

### 11.4 Variables Sensibles

Toutes les variables sensibles sont dans `.env` :
- Clés API (Wassenger, Supabase)
- Secrets JWT
- URLs de connexion

---

## 12. Tests

### 12.1 Backend (Python)

```bash
# Lancer les tests
cd backend
pytest tests/ -v --cov=app

# Tests property-based avec Hypothesis
pytest tests/test_monitoring_properties.py -v
```

#### Tests Property-Based

Le projet utilise **Hypothesis** pour les tests property-based :

```python
@given(
    total_sent=st.integers(min_value=0, max_value=2000),
    interaction_rate=st.floats(min_value=0, max_value=10)
)
def test_remaining_capacity_never_negative(total_sent, interaction_rate):
    """La capacité restante ne doit jamais être négative."""
    capacity = MonitoringService.calculate_remaining_capacity_from_values(
        total_sent, interaction_rate
    )
    assert capacity >= 0
```

### 12.2 Frontend (TypeScript)

```bash
# Lancer les tests
cd frontend
npm run test

# Mode watch
npm run test:watch
```

#### Tests Property-Based

Le projet utilise **fast-check** pour les tests property-based frontend :

```typescript
import fc from 'fast-check';

test('filter preserves valid contacts', () => {
  fc.assert(
    fc.property(
      fc.array(contactArbitrary),
      fc.string(),
      (contacts, search) => {
        const filtered = filterContacts(contacts, search);
        return filtered.every(c => contacts.includes(c));
      }
    )
  );
});
```

---

## 13. Déploiement

### 13.1 Variables d'Environnement

#### Backend (`.env`)

```env
# Environnement
ENVIRONMENT=production
DEBUG=false

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
DATABASE_URL=postgresql://...

# Wassenger
WASSENGER_API_KEY=wsp_...
WASSENGER_DEVICE_ID=dev_...

# Redis
REDIS_URL=rediss://...

# JWT
SECRET_KEY=votre_secret_tres_long

# CORS
ALLOWED_ORIGINS=https://votre-frontend.com
```

#### Frontend (`.env.local`)

```env
NEXT_PUBLIC_API_URL=https://votre-api.com/api
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

### 13.2 Commandes de Démarrage

#### Backend

```bash
# Développement
cd backend
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Celery Beat (tâches périodiques)
celery -A app.tasks.celery_app beat --loglevel=info
```

#### Frontend

```bash
# Développement
cd frontend
npm run dev

# Build production
npm run build
npm run start
```

### 13.3 Services Recommandés

| Service | Recommandation |
|---------|----------------|
| Backend | Render, Railway, Heroku |
| Frontend | Vercel, Netlify |
| Base de données | Supabase |
| Redis | Upstash, Redis Cloud |

---

## 14. État du Projet

### 14.1 Fonctionnalités Implémentées ✅

- [x] Authentification JWT avec rôles
- [x] CRUD complet contacts/catégories/campagnes
- [x] Import CSV de contacts
- [x] Vérification WhatsApp des numéros
- [x] Envoi massif de messages via Wassenger
- [x] Système de Message 1 + Message 2
- [x] Monitoring temps réel avec limite 1000/jour
- [x] Webhooks pour statuts messages
- [x] Dashboard avec statistiques
- [x] Retries automatiques avec backoff
- [x] Récupération automatique après crash
- [x] Tests property-based (backend + frontend)

### 14.2 Points Forts

1. **Robustesse** : Idempotence, retries, recovery automatique
2. **Scalabilité** : Architecture Celery distribuée
3. **Sécurité** : JWT, validation Pydantic, sanitization
4. **Monitoring** : Alertes visuelles, health checks
5. **Tests** : Property-based testing pour la fiabilité

### 14.3 Améliorations Possibles

- [ ] Pagination côté serveur pour les grandes listes
- [ ] Export des statistiques en CSV/PDF
- [ ] Templates de messages réutilisables
- [ ] Planification d'envoi différé
- [ ] Multi-tenant (plusieurs organisations)
- [ ] Intégration avec d'autres canaux (SMS, Email)

---

## 📚 Ressources

### Documentation Externe

- [FastAPI](https://fastapi.tiangolo.com)
- [Next.js](https://nextjs.org/docs)
- [Supabase](https://supabase.com/docs)
- [Wassenger API](https://wassenger.com/docs)
- [Celery](https://docs.celeryq.dev)
- [TanStack Query](https://tanstack.com/query)

### Fichiers de Configuration

| Fichier | Description |
|---------|-------------|
| `backend/.env.example` | Template variables backend |
| `frontend/.env.example` | Template variables frontend |
| `database/schema.sql` | Schéma de base de données |
| `database/rls_policies.sql` | Politiques de sécurité |

---

**Document rédigé par Kiro**  
**Version** : 1.0.0  
**Date** : 27 décembre 2025

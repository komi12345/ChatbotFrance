# 📱 Documentation du Projet - Chatbot WhatsApp

## 📋 Vue d'ensemble

Ce projet est une **plateforme complète de gestion de campagnes WhatsApp** permettant d'envoyer des messages automatisés à des contacts organisés par catégories. Il comprend un backend API REST, un frontend dashboard d'administration, et une intégration avec l'API Wassenger pour l'envoi de messages WhatsApp.

### Fonctionnalités principales

- 🔐 **Authentification** : Système JWT avec rôles (Super Admin / Admin)
- 👥 **Gestion des contacts** : Import, catégorisation, vérification WhatsApp
- 📂 **Catégories** : Organisation des contacts en groupes
- 📣 **Campagnes** : Création et envoi de messages en masse
- 📊 **Statistiques** : Suivi en temps réel (envoyés, délivrés, lus, échoués)
- 🔔 **Monitoring** : Limite quotidienne de 1000 messages avec alertes visuelles
- 🔄 **Webhooks** : Réception des mises à jour de statut WhatsApp

---

## 🏗️ Architecture du Projet

```
projet/
├── backend/           # API REST FastAPI (Python)
├── frontend/          # Dashboard Next.js (React/TypeScript)
├── database/          # Scripts SQL et migrations
├── docs/              # Documentation
└── .kiro/specs/       # Spécifications des fonctionnalités
```

---

## 🔧 Stack Technique

### Backend (Python)

| Technologie | Version | Rôle |
|-------------|---------|------|
| **FastAPI** | ≥0.109.0 | Framework API REST asynchrone |
| **Uvicorn** | ≥0.27.0 | Serveur ASGI haute performance |
| **Pydantic** | ≥2.5.3 | Validation des données et configuration |
| **Supabase** | ≥2.3.4 | Client base de données PostgreSQL |
| **Celery** | ≥5.3.6 | Tâches asynchrones (envoi de messages) |
| **Redis** | ≥5.0.1 | Cache et compteurs temps réel |
| **httpx** | ≥0.26.0 | Client HTTP async pour API Wassenger |
| **python-jose** | ≥3.3.0 | Gestion des tokens JWT |
| **passlib/bcrypt** | ≥1.7.4 | Hachage des mots de passe |
| **Hypothesis** | ≥6.92.0 | Tests property-based |

### Frontend (TypeScript/React)

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Next.js** | 16.0.4 | Framework React avec SSR |
| **React** | 19.2.0 | Bibliothèque UI |
| **TypeScript** | ≥5.9.3 | Typage statique |
| **TanStack Query** | ≥5.90.11 | Gestion du cache et des requêtes API |
| **Axios** | ≥1.13.2 | Client HTTP |
| **Tailwind CSS** | v4 | Framework CSS utilitaire |
| **Radix UI** | - | Composants UI accessibles |
| **Recharts** | ≥3.5.0 | Graphiques et visualisations |
| **Zod** | ≥4.1.13 | Validation des formulaires |
| **React Hook Form** | ≥7.66.1 | Gestion des formulaires |
| **Vitest** | ≥4.0.15 | Framework de tests |
| **fast-check** | ≥4.4.0 | Tests property-based |

### Base de Données

| Technologie | Rôle |
|-------------|------|
| **Supabase** | Backend-as-a-Service (PostgreSQL hébergé) |
| **PostgreSQL** | Base de données relationnelle |
| **Redis** | Stockage des compteurs temps réel |

### Intégration WhatsApp

| Service | Rôle |
|---------|------|
| **Wassenger API** | Envoi de messages WhatsApp |
| **Webhooks** | Réception des statuts (délivré, lu, échoué) |

---

## 📁 Structure Détaillée

### Backend (`backend/`)

```
backend/
├── app/
│   ├── config.py           # Configuration (variables d'environnement)
│   ├── main.py             # Point d'entrée FastAPI
│   ├── database.py         # Connexion base de données
│   ├── supabase_client.py  # Client Supabase
│   ├── models/             # Modèles de données
│   │   ├── user.py         # Utilisateurs (Admin/Super Admin)
│   │   ├── contact.py      # Contacts WhatsApp
│   │   ├── category.py     # Catégories de contacts
│   │   ├── campaign.py     # Campagnes de messages
│   │   ├── message.py      # Messages individuels
│   │   └── interaction.py  # Interactions (réponses, lectures)
│   ├── routers/            # Endpoints API
│   │   ├── auth.py         # Authentification (/api/auth/*)
│   │   ├── contacts.py     # Gestion contacts (/api/contacts/*)
│   │   ├── categories.py   # Gestion catégories (/api/categories/*)
│   │   ├── campaigns.py    # Gestion campagnes (/api/campaigns/*)
│   │   ├── messages.py     # Gestion messages (/api/messages/*)
│   │   ├── users.py        # Gestion utilisateurs (/api/users/*)
│   │   ├── webhooks.py     # Webhooks Wassenger (/api/webhooks/*)
│   │   ├── verify.py       # Vérification WhatsApp (/api/verify/*)
│   │   └── monitoring.py   # Monitoring (/api/monitoring/*)
│   ├── services/           # Logique métier
│   │   ├── wassenger_service.py   # Intégration API Wassenger
│   │   ├── message_service.py     # Gestion des campagnes
│   │   ├── monitoring_service.py  # Compteurs et alertes
│   │   ├── auth_service.py        # Authentification JWT
│   │   └── automation_service.py  # Automatisation Message 2
│   ├── tasks/              # Tâches Celery
│   │   ├── celery_app.py   # Configuration Celery
│   │   └── message_tasks.py # Tâches d'envoi de messages
│   ├── schemas/            # Schémas Pydantic (validation)
│   └── utils/              # Utilitaires
│       ├── security.py     # Fonctions de sécurité
│       ├── validators.py   # Validateurs personnalisés
│       └── constants.py    # Constantes
├── tests/                  # Tests unitaires et property-based
├── requirements.txt        # Dépendances Python
└── pytest.ini              # Configuration pytest
```

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── app/                # Pages Next.js (App Router)
│   │   ├── login/          # Page de connexion
│   │   ├── dashboard/      # Tableau de bord principal
│   │   │   └── monitoring/ # Page de monitoring
│   │   ├── contacts/       # Gestion des contacts
│   │   │   └── import/     # Import de contacts
│   │   ├── categories/     # Gestion des catégories
│   │   ├── campaigns/      # Gestion des campagnes
│   │   │   ├── new/        # Création de campagne
│   │   │   └── [id]/       # Détail d'une campagne
│   │   ├── messages/       # Historique des messages
│   │   ├── statistics/     # Statistiques globales
│   │   └── admin-users/    # Gestion des utilisateurs (Super Admin)
│   ├── components/         # Composants React réutilisables
│   │   ├── ui/             # Composants UI de base (Radix)
│   │   ├── common/         # Composants communs (Loading, Error, etc.)
│   │   ├── layout/         # Layout et navigation
│   │   ├── dashboard/      # Composants du dashboard
│   │   ├── contacts/       # Composants contacts
│   │   ├── categories/     # Composants catégories
│   │   ├── campaigns/      # Composants campagnes
│   │   ├── monitoring/     # Composants monitoring
│   │   └── wassenger/      # Composants spécifiques Wassenger
│   ├── hooks/              # Hooks React personnalisés
│   │   ├── useAuth.ts      # Authentification
│   │   ├── useContacts.ts  # Gestion contacts
│   │   ├── useCategories.ts # Gestion catégories
│   │   ├── useCampaigns.ts # Gestion campagnes
│   │   ├── useMessages.ts  # Gestion messages
│   │   ├── useMonitoring.ts # Monitoring
│   │   └── useStats.ts     # Statistiques
│   ├── lib/                # Utilitaires
│   │   ├── api.ts          # Client Axios configuré
│   │   ├── supabase.ts     # Client Supabase
│   │   └── utils.ts        # Fonctions utilitaires
│   ├── types/              # Types TypeScript
│   └── __tests__/          # Tests frontend
├── package.json            # Dépendances npm
└── vitest.config.ts        # Configuration Vitest
```

### Base de Données (`database/`)

```
database/
├── schema.sql              # Schéma complet des tables
├── migrations/             # Scripts de migration
│   ├── 001_add_whatsapp_verification.sql
│   └── 002_add_monitoring_tables.sql
├── rls_policies.sql        # Politiques Row Level Security
├── seed_admin.sql          # Données initiales (admin)
└── seed_superadmin.sql     # Données initiales (super admin)
```

---

## 🗄️ Modèle de Données

### Tables Principales

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   users     │     │   categories    │     │  contacts   │
├─────────────┤     ├─────────────────┤     ├─────────────┤
│ id          │◄────│ created_by      │     │ id          │
│ email       │     │ id              │◄───┐│ phone_number│
│ password    │     │ name            │    ││ full_number │
│ role        │     │ color           │    ││ first_name  │
│ is_active   │     └─────────────────┘    ││ last_name   │
└─────────────┘              │             ││ whatsapp_   │
      │                      │             ││   verified  │
      │              ┌───────┴───────┐     │└─────────────┘
      │              │category_      │     │
      │              │contacts       │     │
      │              ├───────────────┤     │
      │              │ category_id   │─────┘
      │              │ contact_id    │──────┘
      │              └───────────────┘
      │
      │         ┌─────────────────┐     ┌─────────────┐
      │         │   campaigns     │     │  messages   │
      │         ├─────────────────┤     ├─────────────┤
      └────────►│ created_by      │     │ campaign_id │
                │ id              │◄────│ contact_id  │
                │ name            │     │ content     │
                │ message_1       │     │ status      │
                │ message_2       │     │ whatsapp_   │
                │ status          │     │   message_id│
                │ total_recipients│     └─────────────┘
                └─────────────────┘
                        │
                ┌───────┴───────┐
                │ interactions  │
                ├───────────────┤
                │ campaign_id   │
                │ contact_id    │
                │ message_id    │
                │ type (reply,  │
                │  delivered,   │
                │  read)        │
                └───────────────┘
```

### Statuts des Messages

| Statut | Description |
|--------|-------------|
| `pending` | En attente d'envoi |
| `sent` | Envoyé à WhatsApp |
| `delivered` | Délivré au destinataire |
| `read` | Lu par le destinataire |
| `failed` | Échec d'envoi |

---

## 🔄 Flux de Fonctionnement

### 1. Création et Envoi d'une Campagne

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Admin      │    │   Backend    │    │   Wassenger  │
│  (Frontend)  │    │   (FastAPI)  │    │     API      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │ 1. Créer campagne │                   │
       │──────────────────►│                   │
       │                   │                   │
       │ 2. Sélectionner   │                   │
       │    catégories     │                   │
       │──────────────────►│                   │
       │                   │                   │
       │ 3. Lancer envoi   │                   │
       │──────────────────►│                   │
       │                   │                   │
       │                   │ 4. Celery Task    │
       │                   │    (async)        │
       │                   │                   │
       │                   │ 5. Pour chaque    │
       │                   │    contact:       │
       │                   │    POST /messages │
       │                   │──────────────────►│
       │                   │                   │
       │                   │ 6. Message envoyé │
       │                   │◄──────────────────│
       │                   │                   │
       │ 7. Stats mises    │                   │
       │    à jour         │                   │
       │◄──────────────────│                   │
```

### 2. Réception des Webhooks (Statuts)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   WhatsApp   │    │   Wassenger  │    │   Backend    │
│ (Destinataire)│   │     API      │    │   (FastAPI)  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │ 1. Message reçu   │                   │
       │──────────────────►│                   │
       │                   │                   │
       │                   │ 2. Webhook:       │
       │                   │    delivered      │
       │                   │──────────────────►│
       │                   │                   │
       │                   │                   │ 3. Update BDD
       │                   │                   │    status=delivered
       │                   │                   │
       │ 4. Message lu     │                   │
       │──────────────────►│                   │
       │                   │                   │
       │                   │ 5. Webhook:       │
       │                   │    read           │
       │                   │──────────────────►│
       │                   │                   │
       │                   │                   │ 6. Update BDD
       │                   │                   │    status=read
```

---

## 📊 Système de Monitoring

### Limite Quotidienne

- **Limite** : 1000 messages par jour
- **Compteurs Redis** : Temps réel avec TTL de 48h
- **Persistance** : Synchronisation vers Supabase

### Niveaux d'Alerte

| Niveau | Plage | Couleur | Action |
|--------|-------|---------|--------|
| OK | 0-750 (0-75%) | 🟢 Vert | Envoi normal |
| ATTENTION | 751-900 (76-90%) | 🟡 Jaune | Avertissement |
| DANGER | 901-1000 (91-100%) | 🔴 Rouge | Limite proche |
| BLOCKED | >1000 | ⚫ Gris | Envoi bloqué |

---

## 🚀 Démarrage du Projet

### Prérequis

- Python 3.11+
- Node.js 18+
- Redis
- Compte Supabase
- Compte Wassenger

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # Configurer les variables
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Variables d'Environnement Requises

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://...

# Wassenger
WASSENGER_API_KEY=wsp_live_xxx
WASSENGER_DEVICE_ID=xxx

# JWT
SECRET_KEY=votre-secret-key

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## 🧪 Tests

### Backend (pytest + Hypothesis)

```bash
cd backend
pytest tests/ -v
```

### Frontend (Vitest + fast-check)

```bash
cd frontend
npm run test
```

---

## 📚 Documentation Complémentaire

- [Configuration Wassenger](./GUIDE_CONFIGURATION_WASSENGER_2025.md)
- [Lancement Local](./GUIDE-LANCEMENT-LOCAL-COMPLET.md)
- [Déploiement](./04-DEPLOIEMENT-GRATUIT.md)
- [Templates WhatsApp](./TEMPLATES-WHATSAPP.md)

---

*Documentation générée le 21 décembre 2025*

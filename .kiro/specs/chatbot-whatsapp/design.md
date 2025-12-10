# Document de Conception - Chatbot WhatsApp

## Vue d'Ensemble

Le système de chatbot WhatsApp est une application full-stack composée de trois couches principales :

1. **Frontend Dashboard** : Application Next.js 14+ avec App Router offrant une interface d'administration moderne et responsive
2. **Backend API** : Serveur FastAPI (Python) gérant la logique métier, l'intégration WhatsApp et les tâches asynchrones
3. **Couche de Données** : Base de données PostgreSQL hébergée sur Supabase avec Row Level Security

Le système s'intègre avec WhatsApp Business API (Meta Cloud API) pour l'envoi de messages et la réception de webhooks. Les tâches asynchrones (envois massifs, retries) sont gérées par Celery avec Redis comme message broker.

### Objectifs de Conception

- **Sécurité** : Authentification JWT, hashage bcrypt, RLS Supabase, validation complète des données
- **Performance** : Pagination, indexation DB, caching avec React Query, traitement asynchrone
- **Scalabilité** : Architecture découplée, tâches asynchrones, rate limiting
- **Maintenabilité** : Code commenté en français, séparation des responsabilités, structure modulaire
- **Expérience Utilisateur** : Interface moderne avec shadcn/ui, feedback temps réel, responsive design

## Architecture

### Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                     UTILISATEURS                             │
│              (Super Admin / Admin)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js 14+)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Pages      │  │  Components  │  │    Hooks     │      │
│  │  (App Router)│  │  (shadcn/ui) │  │ (React Query)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ REST API (Axios)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routers    │  │   Services   │  │    Models    │      │
│  │   (API)      │  │  (Business)  │  │ (SQLAlchemy) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Schemas    │  │    Utils     │                        │
│  │  (Pydantic)  │  │  (Security)  │                        │
│  └──────────────┘  └──────────────┘                        │
└────────┬───────────────────────┬────────────────────────────┘
         │                       │
         │                       │ Webhooks
         ▼                       ▼
┌──────────────────┐    ┌──────────────────────┐
│   SUPABASE       │    │  WhatsApp Business   │
│   (PostgreSQL)   │    │   API (Meta Cloud)   │
│                  │    │                      │
│  - Tables        │    │  - Send Messages     │
│  - RLS Policies  │    │  - Receive Webhooks  │
│  - Indexes       │    │  - Templates         │
└──────────────────┘    └──────────────────────┘
         ▲
         │
         │
┌────────┴──────────────────────────────────────┐
│         CELERY WORKERS                        │
│  ┌──────────────┐  ┌──────────────┐          │
│  │ Message Send │  │    Retry     │          │
│  │    Tasks     │  │    Tasks     │          │
│  └──────────────┘  └──────────────┘          │
└────────────────────────┬──────────────────────┘
                         │
                         │ Message Queue
                         ▼
                  ┌──────────────┐
                  │    REDIS     │
                  │ (Message     │
                  │  Broker)     │
                  └──────────────┘
```

### Flux de Données Principaux

#### 1. Flux d'Authentification
```
User → Login Form → POST /api/auth/login → Validate Credentials
→ Generate JWT → Return Token → Store in localStorage → Access Dashboard
```

#### 2. Flux d'Envoi de Message
```
Admin → Select Category → Configure Message → Click Send
→ POST /api/campaigns → Create Campaign → Create Celery Task
→ Celery Worker → Batch Process (25/min) → WhatsApp API
→ Update Message Status → Webhook Received → Update Interactions
→ Trigger Message 2 (if applicable)
```

#### 3. Flux de Webhook
```
WhatsApp → POST /api/webhooks/whatsapp → Validate Token
→ Parse Payload → Identify Contact → Check Automation Rules
→ Create Celery Task for Message 2 → Update Interactions Table
→ Return 200 OK
```

## Composants et Interfaces

### Frontend (Next.js)

#### Structure des Dossiers
```
frontend/src/
├── app/
│   ├── layout.tsx                 # Layout principal avec sidebar
│   ├── page.tsx                   # Redirection vers /dashboard
│   ├── login/
│   │   └── page.tsx              # Page de connexion
│   ├── dashboard/
│   │   └── page.tsx              # Dashboard statistiques
│   ├── categories/
│   │   ├── page.tsx              # Liste des catégories
│   │   └── [id]/page.tsx         # Détails d'une catégorie
│   ├── contacts/
│   │   ├── page.tsx              # Liste des contacts
│   │   └── import/page.tsx       # Import CSV
│   ├── campaigns/
│   │   ├── page.tsx              # Liste des campagnes
│   │   ├── new/page.tsx          # Nouvelle campagne
│   │   └── [id]/page.tsx         # Détails campagne
│   ├── statistics/
│   │   └── page.tsx              # Statistiques détaillées
│   └── admin-users/              # Super Admin uniquement
│       └── page.tsx              # Gestion utilisateurs
├── components/
│   ├── ui/                       # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── dialog.tsx
│   │   ├── table.tsx
│   │   └── ...
│   ├── layout/
│   │   ├── Sidebar.tsx           # Navigation latérale
│   │   ├── Header.tsx            # En-tête avec profil
│   │   └── ProtectedRoute.tsx    # HOC pour routes protégées
│   ├── categories/
│   │   ├── CategoryCard.tsx      # Carte catégorie avec gradient
│   │   ├── CategoryForm.tsx      # Formulaire création/édition
│   │   └── CategoryList.tsx      # Liste avec recherche
│   ├── contacts/
│   │   ├── ContactForm.tsx       # Formulaire avec indicatif pays
│   │   ├── ContactTable.tsx      # Table avec pagination
│   │   └── ContactImport.tsx     # Import CSV
│   ├── campaigns/
│   │   ├── CampaignForm.tsx      # Configuration campagne
│   │   ├── MessageEditor.tsx     # Éditeur Message 1 & 2
│   │   ├── MessagePreview.tsx    # Prévisualisation WhatsApp
│   │   └── CampaignStats.tsx     # Statistiques campagne
│   ├── dashboard/
│   │   ├── StatsCard.tsx         # Carte métrique
│   │   ├── LineChart.tsx         # Graphique évolution
│   │   ├── PieChart.tsx          # Graphique répartition
│   │   └── RecentMessages.tsx    # Historique récent
│   └── common/
│       ├── LoadingSpinner.tsx    # Indicateur chargement
│       ├── ErrorMessage.tsx      # Message d'erreur
│       └── ConfirmDialog.tsx     # Dialog de confirmation
├── lib/
│   ├── api.ts                    # Client Axios configuré
│   ├── supabase.ts               # Client Supabase
│   ├── utils.ts                  # Fonctions utilitaires
│   └── constants.ts              # Constantes (indicatifs pays)
├── hooks/
│   ├── useAuth.ts                # Hook authentification
│   ├── useCategories.ts          # Hook gestion catégories
│   ├── useContacts.ts            # Hook gestion contacts
│   ├── useCampaigns.ts           # Hook gestion campagnes
│   └── useStats.ts               # Hook statistiques
└── types/
    ├── auth.ts                   # Types authentification
    ├── category.ts               # Types catégories
    ├── contact.ts                # Types contacts
    ├── campaign.ts               # Types campagnes
    └── message.ts                # Types messages
```

#### Composants Clés

**1. Sidebar.tsx**
- Navigation principale avec icônes
- Affichage conditionnel selon le rôle (Super Admin vs Admin)
- Highlight de la page active
- Bouton déconnexion

**2. CategoryCard.tsx**
- Affichage avec gradient de couleur aléatoire
- Nombre de contacts
- Date du dernier envoi
- Actions : Éditer, Supprimer, Voir détails

**3. MessageEditor.tsx**
- Deux zones de texte : Message 1 et Message 2
- Boutons pour insérer des liens
- Validation en temps réel
- Compteur de caractères
- Prévisualisation live

**4. ContactForm.tsx**
- Select d'indicatif pays avec recherche
- Input numéro avec validation
- Sélection multiple de catégories
- Validation format international

**5. CampaignStats.tsx**
- Métriques : Total envoyés, Réussis, Échoués, Taux de réussite
- Liste détaillée par contact avec statut
- Bouton retry pour les échecs
- Export CSV

### Backend (FastAPI)

#### Structure des Dossiers
```
backend/app/
├── main.py                       # Point d'entrée FastAPI
├── config.py                     # Configuration (env vars)
├── database.py                   # Connexion DB et session
├── models/
│   ├── __init__.py
│   ├── user.py                   # Modèle User (Super Admin/Admin)
│   ├── category.py               # Modèle Category
│   ├── contact.py                # Modèle Contact
│   ├── campaign.py               # Modèle Campaign
│   ├── message.py                # Modèle Message (tracking)
│   └── interaction.py            # Modèle Interaction (webhooks)
├── schemas/
│   ├── __init__.py
│   ├── user.py                   # Schémas Pydantic User
│   ├── category.py               # Schémas Pydantic Category
│   ├── contact.py                # Schémas Pydantic Contact
│   ├── campaign.py               # Schémas Pydantic Campaign
│   ├── message.py                # Schémas Pydantic Message
│   └── auth.py                   # Schémas Pydantic Auth (Token)
├── routers/
│   ├── __init__.py
│   ├── auth.py                   # Routes authentification
│   ├── categories.py             # CRUD catégories
│   ├── contacts.py               # CRUD contacts + import CSV
│   ├── campaigns.py              # CRUD campagnes + envoi
│   ├── messages.py               # Récupération messages/stats
│   ├── webhooks.py               # Endpoint webhook WhatsApp
│   └── users.py                  # Gestion users (Super Admin)
├── services/
│   ├── __init__.py
│   ├── auth_service.py           # Logique authentification
│   ├── whatsapp_service.py       # Intégration WhatsApp API
│   ├── message_service.py        # Logique envoi messages
│   └── automation_service.py     # Logique automatisation
├── tasks/
│   ├── __init__.py
│   ├── celery_app.py             # Configuration Celery
│   └── message_tasks.py          # Tâches Celery (envoi, retry)
└── utils/
    ├── __init__.py
    ├── security.py               # JWT, hashing, validation
    ├── validators.py             # Validateurs personnalisés
    └── constants.py              # Constantes (codes pays)
```

#### Services Principaux

**1. auth_service.py**
```python
# Fonctions principales :
- authenticate_user(email, password) -> User | None
- create_access_token(data: dict) -> str
- get_current_user(token: str) -> User
- verify_super_admin(user: User) -> bool
- hash_password(password: str) -> str
- verify_password(plain: str, hashed: str) -> bool
```

**2. whatsapp_service.py**
```python
# Fonctions principales :
- send_template_message(phone: str, template_name: str, params: list) -> dict
- send_text_message(phone: str, text: str) -> dict
- verify_webhook(token: str, challenge: str) -> str | None
- parse_webhook_payload(payload: dict) -> Interaction
- get_message_status(message_id: str) -> str
```

**3. message_service.py**
```python
# Fonctions principales :
- create_campaign(name: str, categories: list, message: str) -> Campaign
- send_campaign_messages(campaign_id: int) -> None
- get_campaign_stats(campaign_id: int) -> dict
- retry_failed_messages(campaign_id: int) -> None
- calculate_success_rate(campaign_id: int) -> float
```

**4. automation_service.py**
```python
# Fonctions principales :
- should_send_message_2(contact_id: int, campaign_id: int) -> bool
- trigger_message_2(contact_id: int, campaign_id: int) -> None
- reset_automation_sequence(contact_id: int) -> None
- log_interaction(contact_id: int, campaign_id: int, type: str) -> Interaction
```

#### Routers (Endpoints API)

**auth.py**
- `POST /api/auth/login` - Connexion utilisateur
- `POST /api/auth/refresh` - Rafraîchir le token
- `GET /api/auth/me` - Obtenir l'utilisateur courant

**categories.py**
- `GET /api/categories` - Liste des catégories (pagination)
- `POST /api/categories` - Créer une catégorie
- `GET /api/categories/{id}` - Détails d'une catégorie
- `PUT /api/categories/{id}` - Modifier une catégorie
- `DELETE /api/categories/{id}` - Supprimer une catégorie
- `POST /api/categories/{id}/contacts` - Ajouter des contacts
- `DELETE /api/categories/{id}/contacts/{contact_id}` - Retirer un contact

**contacts.py**
- `GET /api/contacts` - Liste des contacts (pagination, recherche)
- `POST /api/contacts` - Créer un contact
- `POST /api/contacts/import` - Importer CSV
- `GET /api/contacts/{id}` - Détails d'un contact
- `PUT /api/contacts/{id}` - Modifier un contact
- `DELETE /api/contacts/{id}` - Supprimer un contact

**campaigns.py**
- `GET /api/campaigns` - Liste des campagnes (pagination)
- `POST /api/campaigns` - Créer et lancer une campagne
- `GET /api/campaigns/{id}` - Détails d'une campagne
- `GET /api/campaigns/{id}/stats` - Statistiques détaillées
- `POST /api/campaigns/{id}/retry` - Réessayer les échecs

**messages.py**
- `GET /api/messages` - Liste des messages (filtres, pagination)
- `GET /api/messages/{id}` - Détails d'un message
- `GET /api/messages/stats` - Statistiques globales

**webhooks.py**
- `GET /api/webhooks/whatsapp` - Vérification webhook (Meta)
- `POST /api/webhooks/whatsapp` - Réception webhook

**users.py** (Super Admin uniquement)
- `GET /api/users` - Liste des utilisateurs Admin
- `POST /api/users` - Créer un Admin
- `PUT /api/users/{id}` - Modifier un Admin
- `DELETE /api/users/{id}` - Supprimer un Admin

## Modèles de Données

### Schéma de Base de Données

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
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    full_number VARCHAR(25) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table de jonction category_contacts (many-to-many)
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
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'sending', 'completed', 'failed')),
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table de jonction campaign_categories
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
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
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
    message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    interaction_type VARCHAR(50) CHECK (interaction_type IN ('reply', 'reaction', 'read', 'delivered')),
    content TEXT,
    whatsapp_message_id VARCHAR(255),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes pour performance
CREATE INDEX idx_contacts_phone ON contacts(full_number);
CREATE INDEX idx_messages_campaign ON messages(campaign_id);
CREATE INDEX idx_messages_contact ON messages(contact_id);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_interactions_campaign ON interactions(campaign_id);
CREATE INDEX idx_interactions_contact ON interactions(contact_id);
CREATE INDEX idx_category_contacts_category ON category_contacts(category_id);
CREATE INDEX idx_category_contacts_contact ON category_contacts(contact_id);
```

### Row Level Security (RLS) Supabase

```sql
-- Activer RLS sur toutes les tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

-- Politique pour users : Super Admin voit tout, Admin voit seulement son profil
CREATE POLICY users_select_policy ON users
    FOR SELECT
    USING (
        auth.jwt() ->> 'role' = 'super_admin'
        OR id = (auth.jwt() ->> 'user_id')::integer
    );

-- Politique pour categories : Admin voit ses catégories
CREATE POLICY categories_select_policy ON categories
    FOR SELECT
    USING (created_by = (auth.jwt() ->> 'user_id')::integer);

CREATE POLICY categories_insert_policy ON categories
    FOR INSERT
    WITH CHECK (created_by = (auth.jwt() ->> 'user_id')::integer);

-- Politique pour contacts : Admin voit ses contacts
CREATE POLICY contacts_select_policy ON contacts
    FOR SELECT
    USING (created_by = (auth.jwt() ->> 'user_id')::integer);

-- Politique pour campaigns : Admin voit ses campagnes
CREATE POLICY campaigns_select_policy ON campaigns
    FOR SELECT
    USING (created_by = (auth.jwt() ->> 'user_id')::integer);

-- Politique pour messages : Admin voit les messages de ses campagnes
CREATE POLICY messages_select_policy ON messages
    FOR SELECT
    USING (
        campaign_id IN (
            SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
    );

-- Politique pour interactions : Admin voit les interactions de ses campagnes
CREATE POLICY interactions_select_policy ON interactions
    FOR SELECT
    USING (
        campaign_id IN (
            SELECT id FROM campaigns WHERE created_by = (auth.jwt() ->> 'user_id')::integer
        )
    );
```

### Modèles SQLAlchemy

**user.py**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'super_admin' ou 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    categories = relationship("Category", back_populates="creator")
    contacts = relationship("Contact", back_populates="creator")
    campaigns = relationship("Campaign", back_populates="creator")
```

**category.py**
```python
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    color = Column(String(50))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    creator = relationship("User", back_populates="categories")
    contacts = relationship("Contact", secondary="category_contacts", back_populates="categories")
    campaigns = relationship("Campaign", secondary="campaign_categories", back_populates="categories")
```

**contact.py**
```python
class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False)
    country_code = Column(String(5), nullable=False)
    full_number = Column(String(25), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    creator = relationship("User", back_populates="contacts")
    categories = relationship("Category", secondary="category_contacts", back_populates="contacts")
    messages = relationship("Message", back_populates="contact")
    interactions = relationship("Interaction", back_populates="contact")
```

**campaign.py**
```python
class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    message_1 = Column(Text, nullable=False)
    message_2 = Column(Text)
    template_name = Column(String(100))
    status = Column(String(50), default='draft')
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    interaction_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    creator = relationship("User", back_populates="campaigns")
    categories = relationship("Category", secondary="campaign_categories", back_populates="campaigns")
    messages = relationship("Message", back_populates="campaign")
    interactions = relationship("Interaction", back_populates="campaign")
```

**message.py**
```python
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    message_type = Column(String(20))  # 'message_1' ou 'message_2'
    content = Column(Text, nullable=False)
    status = Column(String(50), default='pending')
    whatsapp_message_id = Column(String(255))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    campaign = relationship("Campaign", back_populates="messages")
    contact = relationship("Contact", back_populates="messages")
    interactions = relationship("Interaction", back_populates="message")
```

**interaction.py**
```python
class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    interaction_type = Column(String(50))  # 'reply', 'reaction', 'read', 'delivered'
    content = Column(Text)
    whatsapp_message_id = Column(String(255))
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    campaign = relationship("Campaign", back_populates="interactions")
    contact = relationship("Contact", back_populates="interactions")
    message = relationship("Message", back_populates="interactions")
```



## Propriétés de Correction

*Une propriété est une caractéristique ou un comportement qui devrait être vrai pour toutes les exécutions valides d'un système - essentiellement, une déclaration formelle sur ce que le système devrait faire. Les propriétés servent de pont entre les spécifications lisibles par l'homme et les garanties de correction vérifiables par machine.*

##
### P
ropriété 1 : Validation du format des numéros de téléphone
*Pour tout* contact créé ou modifié, le numéro complet doit correspondre au format international valide avec l'indicatif pays
**Valide : Exigences 2.1, 2.4, 10.6**

### Propriété 2 : Intégrité des associations catégorie-contact
*Pour tout* contact associé à une catégorie, la relation doit exister dans la table category_contacts et être bidirectionnelle
**Valide : Exigences 3.2, 3.3**

### Propriété 3 : Conservation des contacts lors de suppression de catégorie
*Pour toute* catégorie supprimée, tous les contacts associés doivent rester présents dans la table contacts
**Valide : Exigences 3.5**

### Propriété 4 : Respect du rate limiting WhatsApp
*Pour tout* envoi massif de messages, le système ne doit jamais dépasser 25 messages par minute
**Valide : Exigences 4.8**

### Propriété 5 : Déclenchement automatique du Message 2
*Pour tout* contact ayant reçu le Message 1 et ayant interagi, le système doit automatiquement envoyer le Message 2
**Valide : Exigences 4.5, 4.6**

### Propriété 6 : Calcul correct du taux de réussite
*Pour toute* campagne, le taux de réussite doit être égal à (messages réussis / total messages) × 100
**Valide : Exigences 6.5**

### Propriété 7 : Limite de retry à 3 tentatives
*Pour tout* message échoué, le système ne doit jamais effectuer plus de 3 tentatives de renvoi
**Valide : Exigences 7.3**

### Propriété 8 : Délai exponentiel entre les retries
*Pour tout* retry, le délai d'attente doit augmenter exponentiellement (ex: 1min, 2min, 4min)
**Valide : Exigences 7.2**

### Propriété 9 : Validation JWT pour toutes les requêtes protégées
*Pour toute* requête API vers un endpoint protégé sans JWT valide, le système doit retourner une erreur 401
**Valide : Exigences 1.5, 10.4**

### Propriété 10 : Hashage des mots de passe
*Pour tout* mot de passe créé ou modifié, le système doit le hasher avec bcrypt avant stockage
**Valide : Exigences 1.4, 10.3**

### Propriété 11 : Isolation des données par RLS
*Pour tout* Admin, les requêtes ne doivent retourner que les données créées par cet Admin
**Valide : Exigences 1.6**

### Propriété 12 : Pagination des listes
*Pour toute* liste affichée (contacts, campagnes, messages), le système doit implémenter la pagination avec maximum 50 éléments par page
**Valide : Exigences 11.1**

### Propriété 13 : Validation des URLs dans les messages
*Pour toute* URL insérée dans un message, le système doit valider le format avant l'enregistrement
**Valide : Exigences 4.3, 10.7**

### Propriété 14 : Enregistrement des statuts de messages
*Pour tout* message envoyé, le système doit enregistrer le statut avec horodatage dans la table messages
**Valide : Exigences 6.1**

### Propriété 15 : Réponse webhook dans les 20 secondes
*Pour tout* webhook reçu, le système doit retourner un statut 200 OK dans les 20 secondes
**Valide : Exigences 8.5**

## Gestion des Erreurs

### Stratégie Globale

Le système implémente une gestion d'erreurs complète à tous les niveaux :

**Backend (FastAPI)**
- Tous les endpoints sont enveloppés dans des blocs try-except
- Les exceptions sont capturées et loggées avec contexte complet
- Les erreurs sont transformées en réponses HTTP appropriées avec messages clairs
- Utilisation de HTTPException pour les erreurs métier
- Middleware global pour capturer les erreurs non gérées

**Frontend (Next.js)**
- Error boundaries React pour capturer les erreurs de rendu
- Gestion des erreurs dans les hooks React Query
- Affichage de messages d'erreur utilisateur-friendly
- Toast notifications pour les erreurs et succès
- Fallback UI pour les erreurs critiques

### Types d'Erreurs et Gestion

**1. Erreurs de Validation**
- Backend : Pydantic valide automatiquement les schémas
- Frontend : React Hook Form valide les formulaires
- Réponse : 422 Unprocessable Entity avec détails des champs invalides

**2. Erreurs d'Authentification**
- JWT expiré ou invalide
- Identifiants incorrects
- Réponse : 401 Unauthorized avec message explicite

**3. Erreurs d'Autorisation**
- Accès à une ressource non autorisée
- RLS Supabase bloque l'accès
- Réponse : 403 Forbidden

**4. Erreurs de Ressource Non Trouvée**
- Contact, catégorie, campagne inexistant
- Réponse : 404 Not Found

**5. Erreurs WhatsApp API**
- Rate limit dépassé → Retry avec backoff
- Template invalide → Log et notification admin
- Numéro invalide → Marquer comme échoué
- Réponse : 500 Internal Server Error avec log détaillé

**6. Erreurs Base de Données**
- Contrainte unique violée → 409 Conflict
- Connexion perdue → Retry automatique
- Timeout → 504 Gateway Timeout

**7. Erreurs Celery/Redis**
- Redis indisponible → Refuser nouvelles tâches
- Tâche échouée → Retry selon configuration
- Log critique et alerte

### Logging

**Niveaux de Log**
- DEBUG : Détails de développement
- INFO : Actions importantes (création campagne, envoi message)
- WARNING : Situations anormales mais gérables (retry)
- ERROR : Erreurs nécessitant attention (échec API)
- CRITICAL : Erreurs système (Redis down, DB inaccessible)

**Format des Logs**
```python
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "ERROR",
    "service": "whatsapp_service",
    "function": "send_message",
    "user_id": 123,
    "message": "Failed to send message",
    "error": "Rate limit exceeded",
    "context": {
        "campaign_id": 456,
        "contact_id": 789,
        "retry_count": 2
    }
}
```

## Stratégie de Test

### Tests Unitaires

**Backend (pytest)**

Tester chaque service et fonction individuellement :

```python
# Exemple : test_auth_service.py
def test_hash_password():
    """Teste que le hashage bcrypt fonctionne correctement"""
    password = "SecurePass123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) == True

def test_create_access_token():
    """Teste la génération de JWT"""
    data = {"user_id": 1, "role": "admin"}
    token = create_access_token(data)
    assert token is not None
    decoded = decode_token(token)
    assert decoded["user_id"] == 1
```

**Frontend (Jest + React Testing Library)**

Tester les composants et hooks :

```typescript
// Exemple : ContactForm.test.tsx
describe('ContactForm', () => {
  it('valide le format du numéro de téléphone', async () => {
    render(<ContactForm />);
    const input = screen.getByLabelText('Numéro');
    await userEvent.type(input, '123'); // Numéro invalide
    await userEvent.click(screen.getByText('Enregistrer'));
    expect(screen.getByText('Format invalide')).toBeInTheDocument();
  });
});
```

### Tests de Propriétés (Property-Based Testing)

**Framework : Hypothesis (Python)**

Configuration : Minimum 100 itérations par test

```python
# Exemple : test_properties.py
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=20))
def test_property_phone_validation(phone_number):
    """
    Feature: chatbot-whatsapp, Property 1: Validation du format des numéros
    Validates: Requirements 2.1, 2.4, 10.6
    
    Pour tout numéro de téléphone, la validation doit accepter
    uniquement les formats internationaux valides
    """
    result = validate_phone_number(phone_number, "+33")
    if result.is_valid:
        assert result.full_number.startswith("+33")
        assert len(result.full_number) >= 10

@given(st.integers(min_value=1, max_value=1000))
def test_property_success_rate_calculation(total_messages):
    """
    Feature: chatbot-whatsapp, Property 6: Calcul correct du taux de réussite
    Validates: Requirements 6.5
    
    Pour toute campagne, le taux de réussite doit être
    égal à (messages réussis / total messages) × 100
    """
    success_count = random.randint(0, total_messages)
    rate = calculate_success_rate(success_count, total_messages)
    expected = (success_count / total_messages) * 100
    assert abs(rate - expected) < 0.01  # Tolérance pour float

@given(st.integers(min_value=0, max_value=10))
def test_property_retry_limit(retry_count):
    """
    Feature: chatbot-whatsapp, Property 7: Limite de retry à 3 tentatives
    Validates: Requirements 7.3
    
    Pour tout message échoué, le système ne doit jamais
    effectuer plus de 3 tentatives de renvoi
    """
    message = create_test_message(retry_count=retry_count)
    should_retry = should_retry_message(message)
    if retry_count >= 3:
        assert should_retry == False
    else:
        assert should_retry == True
```

### Tests d'Intégration

Tester les flux complets :

**1. Flux d'authentification complet**
- Login → Génération JWT → Accès dashboard → Refresh token

**2. Flux de création de campagne**
- Créer catégorie → Ajouter contacts → Créer campagne → Envoyer messages

**3. Flux de webhook**
- Recevoir webhook → Parser payload → Déclencher Message 2 → Vérifier DB

**4. Flux de retry**
- Message échoue → Retry 1 → Retry 2 → Retry 3 → Marquer échoué définitivement

### Tests End-to-End (E2E)

**Framework : Playwright**

Tester les scénarios utilisateur complets :

```typescript
test('Admin peut créer une campagne et envoyer des messages', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'admin@test.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // Créer catégorie
  await page.goto('/categories');
  await page.click('text=Nouvelle catégorie');
  await page.fill('[name="name"]', 'Test Category');
  await page.click('text=Enregistrer');
  
  // Ajouter contact
  await page.goto('/contacts');
  await page.click('text=Nouveau contact');
  await page.selectOption('[name="country_code"]', '+33');
  await page.fill('[name="phone"]', '612345678');
  await page.click('text=Enregistrer');
  
  // Créer campagne
  await page.goto('/campaigns/new');
  await page.fill('[name="name"]', 'Test Campaign');
  await page.selectOption('[name="category"]', 'Test Category');
  await page.fill('[name="message_1"]', 'Hello from test');
  await page.click('text=Envoyer');
  
  // Vérifier succès
  await expect(page.locator('text=Campagne envoyée')).toBeVisible();
});
```

### Couverture de Tests

**Objectifs de Couverture**
- Backend : Minimum 80% de couverture de code
- Frontend : Minimum 70% de couverture des composants
- Propriétés : 100% des propriétés de correction testées
- E2E : Tous les flux utilisateur critiques couverts

**Outils**
- Backend : pytest-cov
- Frontend : Jest coverage
- Rapports : Intégration CI/CD avec affichage des métriques

## Gestion de la Performance

### Optimisations Base de Données

**Indexes**
```sql
-- Déjà définis dans le schéma
CREATE INDEX idx_contacts_phone ON contacts(full_number);
CREATE INDEX idx_messages_campaign ON messages(campaign_id);
CREATE INDEX idx_messages_status ON messages(status);
```

**Requêtes Optimisées**
- Utiliser des jointures au lieu de requêtes multiples
- Eager loading des relations avec SQLAlchemy
- Pagination systématique des listes

**Connection Pooling**
- SQLAlchemy pool_size=20
- pool_recycle=3600 (1 heure)
- max_overflow=10

### Caching

**React Query (Frontend)**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
});
```

**Redis (Backend)**
- Cache des statistiques dashboard (TTL: 5 minutes)
- Cache des listes de catégories (TTL: 10 minutes)
- Invalidation lors des modifications

### Rate Limiting

**API Backend**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/campaigns")
@limiter.limit("100/minute")
async def create_campaign():
    pass
```

**WhatsApp API**
- Queue Celery avec rate limit 25 msg/min
- Utilisation de Celery beat pour respecter les limites
- Backoff automatique si rate limit atteint

### Monitoring

**Métriques à Suivre**
- Temps de réponse API (p50, p95, p99)
- Taux d'erreur par endpoint
- Nombre de messages en queue Celery
- Utilisation mémoire/CPU
- Taux de succès WhatsApp API

**Outils**
- Logs structurés (JSON)
- Métriques Prometheus (optionnel)
- Alertes sur erreurs critiques

## Sécurité

### Authentification et Autorisation

**JWT Configuration**
- Algorithme : HS256
- Expiration : 30 minutes
- Refresh token : 7 jours
- Secret key : Variable d'environnement (minimum 32 caractères)

**Hashage Mots de Passe**
- Algorithme : bcrypt
- Rounds : 12
- Salt automatique

### Protection CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Validation des Entrées

**Backend**
- Pydantic schemas pour toutes les entrées
- Validation des types, longueurs, formats
- Sanitization des chaînes de caractères

**Frontend**
- React Hook Form avec validation Zod
- Validation côté client avant envoi
- Échappement des caractères spéciaux

### Protection contre les Attaques

**SQL Injection**
- Utilisation exclusive de SQLAlchemy ORM
- Paramètres bindés automatiquement
- Pas de requêtes SQL brutes

**XSS (Cross-Site Scripting)**
- React échappe automatiquement les valeurs
- Validation des URLs avant affichage
- Content Security Policy headers

**CSRF (Cross-Site Request Forgery)**
- Tokens JWT dans headers (pas de cookies)
- Validation de l'origine des requêtes

**Rate Limiting**
- Limite globale : 100 req/min par IP
- Limite login : 5 tentatives/15 min
- Blocage temporaire après abus

## Déploiement

### Architecture de Déploiement

```
┌─────────────────────────────────────────┐
│         Vercel (Frontend)               │
│      Next.js Static + SSR               │
└────────────────┬────────────────────────┘
                 │
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────┐
│    Railway/Render (Backend)             │
│         FastAPI + Celery                │
└────────┬───────────────────┬────────────┘
         │                   │
         │                   │
         ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│    Supabase      │  │  Upstash Redis   │
│   (PostgreSQL)   │  │  (Message Broker)│
└──────────────────┘  └──────────────────┘
```

### Variables d'Environnement Production

**Backend**
```env
# Production
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token

# Redis (Upstash)
REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379

# JWT
SECRET_KEY=your_super_secret_key_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://yourdomain.com
```

**Frontend**
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### Checklist de Déploiement

**Avant le Déploiement**
- [ ] Tous les tests passent
- [ ] Variables d'environnement configurées
- [ ] Secrets sécurisés (pas de hardcode)
- [ ] Base de données migrée
- [ ] Super Admin créé
- [ ] Webhooks WhatsApp configurés
- [ ] CORS configuré pour le domaine production

**Après le Déploiement**
- [ ] Tester l'authentification
- [ ] Tester la création de contact
- [ ] Tester l'envoi de message
- [ ] Vérifier les webhooks
- [ ] Vérifier les logs
- [ ] Tester les retry automatiques
- [ ] Vérifier les statistiques

### Maintenance

**Backups**
- Supabase : Backups automatiques quotidiens
- Export manuel des données critiques hebdomadaire

**Monitoring**
- Logs centralisés
- Alertes sur erreurs critiques
- Surveillance uptime

**Mises à Jour**
- Dépendances : Mise à jour mensuelle
- Sécurité : Patches immédiats
- Features : Déploiement progressif

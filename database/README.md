# Configuration de la Base de Données Supabase

Ce dossier contient tous les scripts SQL nécessaires pour configurer la base de données du chatbot WhatsApp.

## Fichiers

| Fichier | Description |
|---------|-------------|
| `schema.sql` | Schéma complet de la base de données (tables, index, triggers) |
| `rls_policies.sql` | Politiques Row Level Security pour Supabase |
| `seed_superadmin.sql` | Script pour créer le compte Super Admin |
| `seed_admin.sql` | Script pour créer un compte Admin de test |

## Prérequis

1. Un compte Supabase (gratuit sur [supabase.com](https://supabase.com))
2. Un projet Supabase créé

## Instructions d'Installation

### Étape 1 : Créer le projet Supabase

1. Connectez-vous à [Supabase Dashboard](https://app.supabase.com)
2. Cliquez sur "New Project"
3. Configurez :
   - **Name** : `chatbot-whatsapp`
   - **Database Password** : Générez un mot de passe sécurisé (conservez-le!)
   - **Region** : Choisissez la région la plus proche
4. Cliquez sur "Create new project"
5. Attendez que le projet soit prêt (~2 minutes)

### Étape 2 : Exécuter le schéma

1. Dans Supabase Dashboard, allez dans **SQL Editor**
2. Cliquez sur "New query"
3. Copiez-collez le contenu de `schema.sql`
4. Cliquez sur "Run" (ou Ctrl+Enter)
5. Vérifiez qu'il n'y a pas d'erreurs

### Étape 3 : Configurer les politiques RLS

1. Dans SQL Editor, créez une nouvelle requête
2. Copiez-collez le contenu de `rls_policies.sql`
3. Exécutez le script
4. Vérifiez dans **Authentication > Policies** que les politiques sont créées

### Étape 4 : Créer le Super Admin

1. Dans SQL Editor, créez une nouvelle requête
2. Copiez-collez le contenu de `seed_superadmin.sql`
3. **IMPORTANT** : Modifiez le hash du mot de passe avec un hash bcrypt valide
4. Exécutez le script

#### Générer un hash bcrypt

```python
# Installez passlib : pip install passlib[bcrypt]
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "VotreMotDePasseSecurise123!"
hash = pwd_context.hash(password)
print(hash)
```

### Étape 5 : Créer l'Admin de test (optionnel)

Pour le développement uniquement :

1. Exécutez `seed_admin.sql` dans SQL Editor
2. Ce script crée également des données de test

## Récupérer les Clés API

Après la création du projet, récupérez ces informations dans **Settings > API** :

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | URL du projet (ex: `https://xxx.supabase.co`) |
| `SUPABASE_ANON_KEY` | Clé publique pour le frontend |
| `SUPABASE_SERVICE_ROLE_KEY` | Clé secrète pour le backend (bypass RLS) |

## Structure des Tables

```
users
├── id (PK)
├── email (UNIQUE)
├── password_hash
├── role (super_admin | admin)
├── is_active
└── timestamps

categories
├── id (PK)
├── name
├── color
├── created_by (FK → users)
└── timestamps

contacts
├── id (PK)
├── phone_number
├── country_code
├── full_number (UNIQUE)
├── first_name
├── last_name
├── created_by (FK → users)
└── timestamps

category_contacts (M2M)
├── id (PK)
├── category_id (FK)
├── contact_id (FK)
└── added_at

campaigns
├── id (PK)
├── name
├── message_1
├── message_2
├── template_name
├── status
├── counters (total, sent, success, failed, interactions)
├── created_by (FK → users)
└── timestamps

campaign_categories (M2M)
├── id (PK)
├── campaign_id (FK)
└── category_id (FK)

messages
├── id (PK)
├── campaign_id (FK)
├── contact_id (FK)
├── message_type
├── content
├── status
├── whatsapp_message_id
├── error_message
├── retry_count
├── timestamps (sent, delivered, read)
└── timestamps

interactions
├── id (PK)
├── campaign_id (FK)
├── contact_id (FK)
├── message_id (FK)
├── interaction_type
├── content
├── whatsapp_message_id
└── received_at
```

## Sécurité (RLS)

Les politiques Row Level Security garantissent :

- **Super Admin** : Accès complet à toutes les données
- **Admin** : Accès uniquement à ses propres données (catégories, contacts, campagnes)
- **Isolation** : Un Admin ne peut jamais voir les données d'un autre Admin

## Comptes par Défaut

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Super Admin | superadmin@chatbot.local | SuperAdmin123! |
| Admin (test) | admin@chatbot.local | Admin123! |

⚠️ **IMPORTANT** : Changez ces mots de passe immédiatement en production !

## Vérification

Après l'installation, vérifiez :

1. **Tables créées** : 8 tables dans Table Editor
2. **RLS activé** : Icône de cadenas sur chaque table
3. **Politiques** : Vérifiez dans Authentication > Policies
4. **Super Admin** : Testez la connexion via l'API

## Dépannage

### Erreur "relation does not exist"
→ Exécutez `schema.sql` avant les autres scripts

### Erreur "policy already exists"
→ Supprimez les politiques existantes ou ignorez l'erreur

### Erreur de connexion
→ Vérifiez que le projet est bien démarré dans Supabase Dashboard

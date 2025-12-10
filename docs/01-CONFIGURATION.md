# Guide de Configuration - Chatbot WhatsApp

Ce guide détaille les étapes nécessaires pour configurer l'environnement de développement du système de chatbot WhatsApp.

## Table des Matières

1. [Prérequis](#prérequis)
2. [Installation des Dépendances Système](#installation-des-dépendances-système)
3. [Configuration Supabase](#configuration-supabase)
4. [Configuration des Variables d'Environnement](#configuration-des-variables-denvironnement)
5. [Installation des Packages](#installation-des-packages)

---

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants :

- **Python 3.10+** - Pour le backend FastAPI
- **Node.js 18+** - Pour le frontend Next.js
- **Redis** - Pour le message broker Celery
- **Git** - Pour le contrôle de version
- **Compte Supabase** - Pour la base de données PostgreSQL
- **Compte Meta Business** - Pour WhatsApp Business API

---

## Installation des Dépendances Système

### Python 3.10+

**Windows :**
1. Téléchargez Python depuis [python.org](https://www.python.org/downloads/)
2. Exécutez l'installateur et cochez "Add Python to PATH"
3. Vérifiez l'installation :
```bash
python --version
pip --version
```

**macOS :**
```bash
# Avec Homebrew
brew install python@3.11

# Vérification
python3 --version
pip3 --version
```

**Linux (Ubuntu/Debian) :**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Vérification
python3 --version
pip3 --version
```

### Node.js 18+

**Windows :**
1. Téléchargez Node.js LTS depuis [nodejs.org](https://nodejs.org/)
2. Exécutez l'installateur
3. Vérifiez l'installation :
```bash
node --version
npm --version
```

**macOS :**
```bash
# Avec Homebrew
brew install node@18

# Vérification
node --version
npm --version
```

**Linux (Ubuntu/Debian) :**
```bash
# Installation via NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Vérification
node --version
npm --version
```

### Redis

**Windows :**
1. Téléchargez Redis depuis [GitHub Redis for Windows](https://github.com/microsoftarchive/redis/releases)
2. Ou utilisez WSL2 avec Ubuntu et installez Redis :
```bash
sudo apt install redis-server
sudo service redis-server start
```

**macOS :**
```bash
brew install redis
brew services start redis

# Vérification
redis-cli ping
# Réponse attendue : PONG
```

**Linux (Ubuntu/Debian) :**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérification
redis-cli ping
# Réponse attendue : PONG
```

---

## Configuration Supabase

### Étape 1 : Créer un Projet Supabase

1. Rendez-vous sur [supabase.com](https://supabase.com)
2. Connectez-vous ou créez un compte
3. Cliquez sur "New Project"
4. Remplissez les informations :
   - **Name** : chatbot-whatsapp
   - **Database Password** : Générez un mot de passe fort (conservez-le !)
   - **Region** : Choisissez la région la plus proche
5. Cliquez sur "Create new project"
6. Attendez que le projet soit provisionné (2-3 minutes)

### Étape 2 : Récupérer les Identifiants

1. Dans le dashboard Supabase, allez dans **Settings** > **API**
2. Notez les informations suivantes :
   - **Project URL** : `https://xxxxx.supabase.co`
   - **anon public key** : Clé publique pour le frontend
   - **service_role key** : Clé secrète pour le backend (ne jamais exposer côté client !)

3. Allez dans **Settings** > **Database**
4. Notez la **Connection string** (URI) pour PostgreSQL

### Étape 3 : Exécuter le Schéma de Base de Données

1. Dans Supabase, allez dans **SQL Editor**
2. Créez une nouvelle requête
3. Copiez et exécutez le contenu de `database/schema.sql`
4. Exécutez ensuite `database/rls_policies.sql` pour les politiques de sécurité
5. Exécutez `database/seed_superadmin.sql` pour créer le compte Super Admin

> **Note** : Pour générer le hash du mot de passe Super Admin, utilisez le script `database/generate_password_hash.py`

---

## Configuration des Variables d'Environnement

### Backend (.env)

Créez un fichier `.env` dans le dossier `backend/` en copiant `.env.example` :

```bash
cd backend
cp .env.example .env
```

Modifiez les valeurs suivantes :

```env
# Configuration de l'environnement
ENVIRONMENT=development
DEBUG=True

# API
API_HOST=0.0.0.0
API_PORT=8000

# Supabase / PostgreSQL
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_anon_key
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key
DATABASE_URL=postgresql://postgres:[MOT_DE_PASSE]@db.votre-projet.supabase.co:5432/postgres

# WhatsApp Business API (voir guide 02-WHATSAPP-SETUP.md)
WHATSAPP_PHONE_NUMBER_ID=votre_phone_number_id
WHATSAPP_ACCESS_TOKEN=votre_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=un_token_secret_de_votre_choix
WHATSAPP_API_VERSION=v18.0

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT - Générez une clé secrète sécurisée
SECRET_KEY=votre_cle_secrete_minimum_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
WHATSAPP_RATE_LIMIT_PER_MINUTE=25

# Retry Configuration
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY_SECONDS=60
```

#### Génération d'une Clé Secrète JWT

```python
# Exécutez dans un terminal Python
import secrets
print(secrets.token_hex(32))
```

### Frontend (.env.local)

Créez un fichier `.env.local` dans le dossier `frontend/` :

```bash
cd frontend
cp .env.local.example .env.local
```

Modifiez les valeurs :

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_anon_key
```

---

## Installation des Packages

### Backend (Python)

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Frontend (Node.js)

```bash
cd frontend

# Installer les dépendances
npm install
```

---

## Vérification de l'Installation

### Vérifier la Connexion à Supabase

```python
# Dans le dossier backend avec l'environnement virtuel activé
python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Connexion Supabase OK!' if result else 'Erreur')
"
```

### Vérifier Redis

```bash
redis-cli ping
# Réponse attendue : PONG
```

### Vérifier les Variables d'Environnement

```python
# Dans le dossier backend
python -c "
from app.config import settings
print(f'Supabase URL: {settings.SUPABASE_URL}')
print(f'Redis URL: {settings.REDIS_URL}')
print('Configuration OK!')
"
```

---

## Prochaines Étapes

1. **Configuration WhatsApp** : Suivez le guide [02-WHATSAPP-SETUP.md](./02-WHATSAPP-SETUP.md)
2. **Lancement Local** : Suivez le guide [03-LANCEMENT-LOCAL.md](./03-LANCEMENT-LOCAL.md)
3. **Déploiement** : Suivez le guide [04-DEPLOIEMENT-GRATUIT.md](./04-DEPLOIEMENT-GRATUIT.md)

---

## Dépannage

### Erreur "Module not found"
```bash
# Assurez-vous que l'environnement virtuel est activé
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
```

### Erreur de connexion Supabase
- Vérifiez que l'URL et les clés sont correctes
- Vérifiez que le projet Supabase est actif
- Vérifiez que le mot de passe de la base de données est correct dans DATABASE_URL

### Redis ne démarre pas
```bash
# Linux/macOS
sudo systemctl status redis-server
sudo systemctl restart redis-server

# Windows (WSL)
sudo service redis-server restart
```

### Erreur CORS
- Vérifiez que `ALLOWED_ORIGINS` contient l'URL du frontend
- En développement : `http://localhost:3000`

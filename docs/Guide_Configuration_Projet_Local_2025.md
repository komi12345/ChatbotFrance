# 🚀 Guide de Configuration et Lancement Local - Chatbot WhatsApp 2025

Ce guide complet vous accompagne pour configurer et lancer le projet Chatbot WhatsApp en local avec l'intégration **Twilio WhatsApp Sandbox**.

> 📅 **Dernière mise à jour** : Décembre 2025  
> 🔄 **Version** : Migration Twilio WhatsApp Sandbox

---

## 📋 Table des Matières

1. [Prérequis Système](#1-prérequis-système)
2. [Architecture du Projet](#2-architecture-du-projet)
3. [Installation des Dépendances](#3-installation-des-dépendances)
4. [Configuration des Variables d'Environnement](#4-configuration-des-variables-denvironnement)
5. [Configuration de ngrok](#5-configuration-de-ngrok)
6. [Démarrage du Projet](#6-démarrage-du-projet)
7. [Tests d'Envoi de Messages](#7-tests-denvoi-de-messages)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prérequis Système

### Logiciels Requis

| Logiciel | Version Minimum | Vérification | Téléchargement |
|----------|-----------------|--------------|----------------|
| **Python** | 3.10+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | `node --version` | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ | `npm --version` | Inclus avec Node.js |
| **Git** | 2.0+ | `git --version` | [git-scm.com](https://git-scm.com/) |

### Vérification des Prérequis

Ouvrez un terminal (PowerShell ou CMD) et exécutez :

```powershell
# Vérifier Python
python --version
# Attendu : Python 3.10.x ou supérieur

# Vérifier Node.js
node --version
# Attendu : v18.x.x ou supérieur

# Vérifier npm
npm --version
# Attendu : 9.x.x ou supérieur

# Vérifier Git
git --version
# Attendu : git version 2.x.x
```

### Comptes Requis

| Service | Description | Lien |
|---------|-------------|------|
| **Supabase** | Base de données PostgreSQL hébergée (gratuit) | [supabase.com](https://supabase.com) |
| **Twilio** | API WhatsApp Sandbox (gratuit pour les tests) | [twilio.com](https://www.twilio.com) |
| **ngrok** | Tunnel HTTPS pour les webhooks (gratuit) | [ngrok.com](https://ngrok.com) |

---

## 2. Architecture du Projet

### Structure des Dossiers

```
projet-chatbot-whatsapp/
├── backend/                    # API REST FastAPI (Python)
│   ├── app/
│   │   ├── config.py          # Configuration et variables d'environnement
│   │   ├── main.py            # Point d'entrée de l'application
│   │   ├── database.py        # Connexion Supabase
│   │   ├── models/            # Modèles de données
│   │   ├── routers/           # Endpoints API
│   │   ├── schemas/           # Schémas Pydantic
│   │   ├── services/          # Services métier
│   │   │   └── twilio_service.py  # Intégration Twilio WhatsApp
│   │   ├── tasks/             # Tâches Celery (envoi asynchrone)
│   │   └── utils/             # Utilitaires
│   ├── tests/                 # Tests unitaires et property-based
│   ├── .env                   # Variables d'environnement (à créer)
│   ├── .env.example           # Exemple de configuration
│   └── requirements.txt       # Dépendances Python
│
├── frontend/                   # Dashboard Next.js (React)
│   ├── src/
│   │   ├── app/               # Pages (App Router Next.js 14+)
│   │   ├── components/        # Composants React
│   │   ├── hooks/             # Hooks personnalisés
│   │   ├── lib/               # Utilitaires et configuration
│   │   └── types/             # Types TypeScript
│   ├── .env.local             # Variables d'environnement (à créer)
│   ├── .env.local.example     # Exemple de configuration
│   └── package.json           # Dépendances Node.js
│
├── database/                   # Scripts SQL
│   ├── schema.sql             # Schéma de la base de données
│   ├── seed_superadmin.sql    # Création de l'utilisateur admin
│   └── rls_policies.sql       # Politiques de sécurité Row Level Security
│
├── docs/                       # Documentation
│   ├── Configuration_Twilio_WhatsApp_Sandbox_2025.md
│   └── Guide_Configuration_Projet_Local_2025.md  # Ce fichier
│
├── start_backend.bat          # Script de démarrage backend (Windows)
└── start_frontend.bat         # Script de démarrage frontend (Windows)
```

### Architecture Technique

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js 14+)                      │
│  - Dashboard d'administration                                │
│  - Gestion des contacts, campagnes, messages                │
│  - Interface utilisateur responsive                          │
│  - Port : 3000                                               │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (Axios)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                           │
│  - API REST avec documentation Swagger                       │
│  - Authentification JWT                                      │
│  - Service Twilio WhatsApp                                   │
│  - Tâches asynchrones Celery                                │
│  - Port : 8000                                               │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Supabase   │  │   Twilio    │  │   Redis     │
│ PostgreSQL  │  │  WhatsApp   │  │  (Celery)   │
│             │  │   Sandbox   │  │  Optionnel  │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Technologies Utilisées

**Backend :**
- **FastAPI** : Framework web Python moderne et performant
- **Supabase Client** : Connexion à PostgreSQL via API REST
- **Twilio SDK** : Intégration WhatsApp Sandbox
- **Celery** : Tâches asynchrones (optionnel)
- **Pydantic** : Validation des données

**Frontend :**
- **Next.js 14+** : Framework React avec App Router
- **TailwindCSS** : Styling utilitaire
- **React Query** : Gestion du cache et des requêtes
- **Shadcn/ui** : Composants UI accessibles
- **TypeScript** : Typage statique

---

## 3. Installation des Dépendances

### 3.1 Cloner le Projet

```powershell
# Cloner le repository
git clone <url-du-repo>
cd projet-chatbot-whatsapp
```

### 3.2 Installation Backend (Python)

```powershell
# Naviguer vers le dossier backend
cd backend

# Créer un environnement virtuel (recommandé)
python -m venv venv

# Activer l'environnement virtuel
# Windows PowerShell :
.\venv\Scripts\Activate.ps1
# Windows CMD :
venv\Scripts\activate.bat

# Installer les dépendances
pip install -r requirements.txt
```

**Dépendances principales installées :**
- `fastapi>=0.109.0` - Framework web
- `uvicorn>=0.27.0` - Serveur ASGI
- `supabase>=2.3.4` - Client Supabase
- `twilio>=9.0.0` - SDK Twilio WhatsApp
- `pydantic>=2.5.3` - Validation des données
- `python-jose>=3.3.0` - JWT
- `hypothesis>=6.92.0` - Tests property-based

### 3.3 Installation Frontend (Node.js)

```powershell
# Naviguer vers le dossier frontend
cd frontend

# Installer les dépendances
npm install
```

**Dépendances principales installées :**
- `next@16.0.4` - Framework React
- `react@19.2.0` - Bibliothèque UI
- `@tanstack/react-query` - Gestion des requêtes
- `axios` - Client HTTP
- `tailwindcss` - Styling
- `zod` - Validation des schémas

### Problèmes de Compatibilité Courants

**Python :**
```powershell
# Si erreur "pip not found"
python -m pip install --upgrade pip

# Si erreur avec bcrypt sur Windows
pip install bcrypt --no-binary :all:

# Si erreur avec uvloop (Windows)
# uvloop n'est pas supporté sur Windows, c'est normal
```

**Node.js :**
```powershell
# Si erreur de dépendances
rm -rf node_modules
rm package-lock.json
npm install

# Si erreur de version Node.js
# Utilisez nvm pour gérer les versions
nvm install 18
nvm use 18
```

---

## 4. Configuration des Variables d'Environnement

### 4.1 Configuration Backend

Créez le fichier `.env` dans le dossier `backend` :

```powershell
cd backend
copy .env.example .env
```

Ouvrez `backend/.env` et configurez les variables :

```env
# =============================================================================
# ENVIRONNEMENT
# =============================================================================
ENVIRONMENT=development
DEBUG=True

# =============================================================================
# SUPABASE / POSTGRESQL
# =============================================================================
# URL de votre projet Supabase
# Trouvez-la dans : Supabase Dashboard > Settings > API > Project URL
SUPABASE_URL=https://votre-projet.supabase.co

# Clé publique (anon key)
# Trouvez-la dans : Supabase Dashboard > Settings > API > anon public
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Clé de service (service_role key) - CONFIDENTIELLE
# Trouvez-la dans : Supabase Dashboard > Settings > API > service_role
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# URL de connexion PostgreSQL directe
DATABASE_URL=postgresql://postgres:password@db.votre-projet.supabase.co:5432/postgres

# =============================================================================
# TWILIO WHATSAPP SANDBOX (2025)
# =============================================================================
# Account SID Twilio (OBLIGATOIRE)
# Trouvez-le dans : Twilio Console > Account Info
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Auth Token Twilio (OBLIGATOIRE, SECRET)
# Trouvez-le dans : Twilio Console > Account Info > Show
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Numéro Sandbox Twilio (ne pas modifier)
TWILIO_SANDBOX_NUMBER=+14155238886

# URL de base pour les webhooks (votre URL ngrok)
TWILIO_WEBHOOK_BASE_URL=https://votre-url.ngrok.io

# =============================================================================
# AUTHENTIFICATION JWT
# =============================================================================
# Clé secrète pour signer les tokens JWT
# Générez-en une avec : python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=votre_cle_secrete_generee_ici

# Algorithme de signature
ALGORITHM=HS256

# Durée de validité du token (en minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# =============================================================================
# CORS
# =============================================================================
ALLOWED_ORIGINS=http://localhost:3000

# =============================================================================
# REDIS (optionnel pour Celery)
# =============================================================================
REDIS_URL=redis://localhost:6379/0
```

### 4.2 Configuration Frontend

Créez le fichier `.env.local` dans le dossier `frontend` :

```powershell
cd frontend
copy .env.local.example .env.local
```

Ouvrez `frontend/.env.local` et configurez :

```env
# =============================================================================
# API BACKEND
# =============================================================================
# URL de l'API backend FastAPI
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# =============================================================================
# SUPABASE
# =============================================================================
# URL de votre projet Supabase (même valeur que le backend)
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co

# Clé publique (anon key) - même valeur que le backend
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4.3 Vérification de la Configuration

```powershell
cd backend
python -c "
from app.config import settings
print('=== Configuration Backend ===')
print(f'Supabase URL: {settings.SUPABASE_URL}')
print(f'Twilio Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...')
print(f'Twilio Sandbox Number: {settings.TWILIO_SANDBOX_NUMBER}')
print('✅ Configuration OK!')
"
```

---

## 5. Configuration de ngrok

ngrok crée un tunnel HTTPS sécurisé pour recevoir les webhooks Twilio en développement local.

### 5.1 Installation de ngrok

**Option 1 : Téléchargement direct**
1. Téléchargez ngrok : https://ngrok.com/download
2. Extrayez l'archive
3. Placez `ngrok.exe` dans un dossier accessible (ex: `C:\ngrok\`)
4. Ajoutez ce dossier au PATH système

**Option 2 : Via Chocolatey (Windows)**
```powershell
choco install ngrok
```

**Option 3 : Via Scoop (Windows)**
```powershell
scoop install ngrok
```

### 5.2 Créer un Compte ngrok

1. Inscrivez-vous sur https://ngrok.com (gratuit)
2. Connectez-vous au dashboard ngrok
3. Récupérez votre **Authtoken** dans la section "Your Authtoken"

### 5.3 Configurer ngrok

```powershell
# Ajouter votre authtoken
ngrok config add-authtoken VOTRE_AUTHTOKEN
```

### 5.4 Lancer ngrok

**Important** : Le backend doit être lancé sur le port 8000 avant de démarrer ngrok.

```powershell
# Créer un tunnel vers le port 8000
ngrok http 8000
```

Vous verrez une sortie similaire à :

```
Session Status                online
Account                       votre@email.com
Version                       3.x.x
Region                        Europe (eu)
Forwarding                    https://abc123xyz.ngrok-free.app -> http://localhost:8000
```

📝 **Notez l'URL HTTPS** (ex: `https://abc123xyz.ngrok-free.app`)

### 5.5 Configurer les Webhooks Twilio

1. Allez dans le dashboard Twilio : **Develop** > **Messaging** > **Try it out** > **Send a WhatsApp message**
2. Dans la section **"Sandbox Settings"**, configurez :

| Champ | Valeur |
|-------|--------|
| **WHEN A MESSAGE COMES IN** | `https://VOTRE_URL_NGROK/api/webhooks/twilio` |
| **STATUS CALLBACK URL** | `https://VOTRE_URL_NGROK/api/webhooks/twilio` |

3. Cliquez sur **"Save"**

### 5.6 Mettre à jour le Backend

Mettez à jour `TWILIO_WEBHOOK_BASE_URL` dans `backend/.env` :

```env
TWILIO_WEBHOOK_BASE_URL=https://abc123xyz.ngrok-free.app
```

> ⚠️ **Note** : L'URL ngrok change à chaque redémarrage (plan gratuit). Mettez à jour l'URL dans Twilio et le fichier `.env` à chaque fois.

---

## 6. Démarrage du Projet

### Ordre de Démarrage Recommandé

1. **Backend** (port 8000)
2. **ngrok** (tunnel vers port 8000)
3. **Frontend** (port 3000)

### 6.1 Démarrer le Backend

**Option A : Script automatique (Windows)**
```powershell
# Double-cliquez sur start_backend.bat à la racine du projet
```

**Option B : Manuellement**
```powershell
cd backend

# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Lancer le serveur
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ **Vérification** :
- API : http://localhost:8000
- Documentation Swagger : http://localhost:8000/api/docs
- Health Check : http://localhost:8000/api/health

### 6.2 Démarrer ngrok

```powershell
# Dans un nouveau terminal
ngrok http 8000
```

✅ **Vérification** :
- Interface web ngrok : http://127.0.0.1:4040
- Notez l'URL HTTPS fournie

### 6.3 Démarrer le Frontend

**Option A : Script automatique (Windows)**
```powershell
# Double-cliquez sur start_frontend.bat à la racine du projet
```

**Option B : Manuellement**
```powershell
cd frontend
npm run dev
```

✅ **Vérification** :
- Dashboard : http://localhost:3000

### 6.4 Se Connecter à l'Application

Ouvrez http://localhost:3000 et connectez-vous avec :

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| **Super Admin** | `superadmin@chatbot.local` | `SuperAdmin2024!` |
| **Admin** | `admin@chatbot.local` | `Admin2024!` |

---

## 7. Tests d'Envoi de Messages

### 7.1 Préparation du Numéro de Test

Avant d'envoyer des messages, le destinataire doit rejoindre le Sandbox Twilio :

1. **Ouvrez WhatsApp** sur votre téléphone
2. **Envoyez un message** au numéro `+1 415 523 8886`
3. **Contenu du message** : `join <votre-code>`
   - Le code est visible dans le dashboard Twilio (section Sandbox)
   - Exemple : `join purple-elephant`
4. **Attendez la confirmation** de Twilio

### 7.2 Ajouter un Contact de Test

1. Connectez-vous au dashboard (http://localhost:3000)
2. Allez dans **Contacts**
3. Cliquez sur **Ajouter un contact**
4. Remplissez :
   - **Nom** : Votre nom
   - **Téléphone** : Votre numéro WhatsApp (format : +33612345678)
   - **Catégorie** : Sélectionnez une catégorie
5. Sauvegardez

### 7.3 Envoyer un Message de Test

**Via le Dashboard :**
1. Allez dans **Campagnes**
2. Créez une nouvelle campagne
3. Sélectionnez le contact de test
4. Rédigez le message
5. Lancez la campagne

**Via l'API (curl) :**
```powershell
# Test d'envoi direct via l'API Twilio
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/VOTRE_ACCOUNT_SID/Messages.json" `
  -u "VOTRE_ACCOUNT_SID:VOTRE_AUTH_TOKEN" `
  -d "From=whatsapp:+14155238886" `
  -d "To=whatsapp:+33VOTRE_NUMERO" `
  -d "Body=Test depuis le Sandbox Twilio!"
```

### 7.4 Vérifier la Réception

1. **Vérifiez votre WhatsApp** : Le message doit arriver
2. **Vérifiez les logs backend** : Vous devriez voir les logs d'envoi
3. **Vérifiez ngrok** : http://127.0.0.1:4040 montre les webhooks reçus

### 7.5 Tester les Webhooks

1. **Répondez au message** depuis WhatsApp
2. **Vérifiez les logs backend** : Le webhook doit être reçu
3. **Vérifiez le dashboard** : L'interaction doit apparaître

---

## 8. Troubleshooting

Cette section couvre les erreurs courantes et leurs solutions pour vous aider à résoudre rapidement les problèmes.

---

### 8.1 Erreurs Backend

#### Le backend ne démarre pas

**Erreur : Module not found**
```powershell
# Réinstaller les dépendances
cd backend
pip install -r requirements.txt
```

**Erreur : Variables d'environnement manquantes**
```
ValueError: Variables Twilio manquantes: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
```

**Solution :**
```powershell
# Vérifier que .env existe
dir backend\.env

# Vérifier le contenu
type backend\.env

# Copier depuis l'exemple si nécessaire
copy backend\.env.example backend\.env
```

**Erreur : Port 8000 déjà utilisé**
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Solution :**
```powershell
# Trouver le processus utilisant le port
netstat -ano | findstr :8000

# Tuer le processus (remplacez PID par le numéro trouvé)
taskkill /PID <PID> /F

# Ou utiliser un autre port
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Erreur : uvloop not available (Windows)**
```
WARNING: uvloop is not available, using asyncio instead
```

**Solution :** C'est un avertissement normal sur Windows. uvloop n'est pas supporté sur Windows, le backend utilise asyncio à la place. Aucune action requise.

**Erreur : bcrypt installation failed**
```powershell
# Installer les outils de compilation Visual C++
# Ou installer bcrypt sans compilation
pip install bcrypt --no-binary :all:
```

#### Erreur de connexion Supabase

**Erreur : Connection refused / timeout**
```
supabase.lib.client_options.ClientOptions: Connection refused
```

**Solutions :**
1. Vérifiez que votre projet Supabase est actif (pas en pause après 7 jours d'inactivité)
2. Vérifiez les clés API dans `.env`
3. Vérifiez votre connexion internet
4. Testez la connexion :
```powershell
cd backend
python verify_setup.py
```

**Erreur : Invalid API key**
```
AuthApiError: Invalid API key
```

**Solution :**
1. Allez dans Supabase Dashboard > Settings > API
2. Copiez la clé `anon public` pour `SUPABASE_KEY`
3. Copiez la clé `service_role` pour `SUPABASE_SERVICE_ROLE_KEY`
4. Redémarrez le backend

---

### 8.2 Erreurs Frontend

#### Le frontend ne démarre pas

**Erreur : npm packages manquants**
```
Module not found: Can't resolve '@tanstack/react-query'
```

**Solution :**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

**Erreur : Port 3000 déjà utilisé**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution :**
```powershell
# Trouver et tuer le processus
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Ou utiliser un autre port
npm run dev -- -p 3001
```

**Erreur : Version Node.js incompatible**
```
error engine: Unsupported engine
```

**Solution :**
```powershell
# Vérifier la version
node --version

# Installer la bonne version avec nvm
nvm install 18
nvm use 18
```

**Erreur : TypeScript compilation errors**
```
Type error: Cannot find module '@/lib/api'
```

**Solution :**
```powershell
# Nettoyer le cache Next.js
Remove-Item -Recurse -Force frontend\.next
npm run dev
```

---

### 8.3 Erreurs CORS

**Erreur : CORS policy blocked**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/...' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Causes possibles et solutions :**

1. **ALLOWED_ORIGINS mal configuré**
   ```env
   # backend/.env
   ALLOWED_ORIGINS=http://localhost:3000
   ```

2. **Plusieurs origines nécessaires**
   ```env
   # Séparer par des virgules
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
   ```

3. **Backend non redémarré après modification**
   ```powershell
   # Redémarrer le backend après modification du .env
   # Ctrl+C pour arrêter, puis relancer
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Vérifier la configuration CORS dans main.py**
   ```python
   # Le middleware CORS doit être configuré
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.ALLOWED_ORIGINS.split(","),
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

**Test de diagnostic CORS :**
```powershell
# Tester une requête OPTIONS (preflight)
curl -X OPTIONS "http://localhost:8000/api/health" `
  -H "Origin: http://localhost:3000" `
  -H "Access-Control-Request-Method: GET" `
  -v
```

---

### 8.4 Erreurs Réseau

#### Connexion refusée entre frontend et backend

**Erreur : Network Error / ECONNREFUSED**
```
AxiosError: Network Error
```

**Solutions :**

1. **Vérifier que le backend est lancé**
   ```powershell
   # Tester l'accès au backend
   curl http://localhost:8000/api/health
   ```

2. **Vérifier l'URL de l'API dans le frontend**
   ```env
   # frontend/.env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

3. **Vérifier le pare-feu Windows**
   - Ouvrir "Pare-feu Windows Defender"
   - Autoriser Python et Node.js dans les applications autorisées

4. **Vérifier que les ports ne sont pas bloqués**
   ```powershell
   # Tester la connectivité
   Test-NetConnection -ComputerName localhost -Port 8000
   Test-NetConnection -ComputerName localhost -Port 3000
   ```

#### Timeout des requêtes

**Erreur : Request timeout**
```
AxiosError: timeout of 30000ms exceeded
```

**Solutions :**
1. Vérifier la charge du serveur backend
2. Augmenter le timeout dans la configuration Axios
3. Vérifier les requêtes lentes dans les logs backend

---

### 8.5 Erreurs ngrok

#### ngrok ne fonctionne pas

**Erreur : Authtoken invalide**
```
ERR_NGROK_105: Invalid authtoken
```

**Solution :**
```powershell
# Récupérer un nouveau token sur ngrok.com
ngrok config add-authtoken VOTRE_NOUVEAU_TOKEN
```

**Erreur : Tunnel session expired**
```
ERR_NGROK_108: Your ngrok session has expired
```

**Solution :** Relancez ngrok. Les sessions gratuites expirent après quelques heures.

**L'URL change à chaque redémarrage**
- C'est normal avec le plan gratuit
- Mettez à jour l'URL dans Twilio Dashboard et `.env` à chaque fois
- Ou passez à un plan payant pour une URL fixe

**Erreur : Too many connections**
```
ERR_NGROK_108: Only 1 simultaneous ngrok agent session allowed
```

**Solution :**
```powershell
# Fermer toutes les instances ngrok
taskkill /IM ngrok.exe /F

# Relancer une seule instance
ngrok http 8000
```

---

### 8.6 Erreurs Twilio

#### Erreur 63007 : Destinataire non inscrit au Sandbox

```json
{"code": 63007, "message": "Twilio could not find a Channel with the specified From address"}
```

Le destinataire n'a pas rejoint le Sandbox.

**Solution :**
1. Le destinataire ouvre WhatsApp
2. Envoie `join <code>` au +1 415 523 8886
3. Attend la confirmation "You are all set!"
4. Réessayez l'envoi

#### Erreur 21608 : Numéro non vérifié

```json
{"code": 21608, "message": "The 'To' phone number is not currently verified"}
```

**Solution :**
- Utilisez le format international : `+33612345678`
- Pas d'espaces ni de caractères spéciaux
- Le destinataire doit avoir rejoint le Sandbox

#### Erreur 20003 : Authentification échouée

```json
{"code": 20003, "message": "Authentication Error"}
```

Account SID ou Auth Token incorrect.

**Solution :**
1. Allez dans Twilio Console > Account Info
2. Vérifiez Account SID et Auth Token
3. Mettez à jour `backend/.env`
4. Redémarrez le backend

#### Erreur 21211 : Numéro de téléphone invalide

```json
{"code": 21211, "message": "Invalid 'To' Phone Number"}
```

**Solution :**
- Format correct : `+33612345678` (avec indicatif pays)
- Pas de zéro initial après l'indicatif
- Pas d'espaces ou tirets

#### Erreur 30003 : Destination injoignable

```json
{"code": 30003, "message": "Unreachable destination handset"}
```

**Solutions :**
- Le téléphone est peut-être éteint ou hors réseau
- Réessayez plus tard
- Vérifiez que le numéro est correct

#### Erreur 30006 : Numéro fixe ou sans WhatsApp

```json
{"code": 30006, "message": "Landline or unreachable carrier"}
```

**Solution :** Le numéro n'a pas WhatsApp installé. Utilisez un numéro mobile avec WhatsApp.

#### Erreur 63016 : Message trop long

```json
{"code": 63016, "message": "Message body is too long"}
```

**Solution :** Limitez le message à 1600 caractères maximum.

---

### 8.7 Erreurs Webhooks

#### Les webhooks ne sont pas reçus

**Diagnostic :**
1. **Vérifiez ngrok** : Est-il lancé et connecté ?
   ```powershell
   # Vérifier l'interface web ngrok
   # Ouvrez http://127.0.0.1:4040 dans votre navigateur
   ```

2. **Vérifiez l'URL dans Twilio** : L'URL correspond-elle à votre URL ngrok ?
   - Twilio Console > Messaging > Try it out > Send a WhatsApp message > Sandbox Settings

3. **Vérifiez le backend** : Est-il lancé sur le port 8000 ?
   ```powershell
   curl http://localhost:8000/api/health
   ```

4. **Testez manuellement** :
   ```powershell
   curl -X POST "https://VOTRE_URL_NGROK/api/webhooks/twilio" `
     -H "Content-Type: application/x-www-form-urlencoded" `
     -d "From=whatsapp:+33612345678&Body=test&MessageSid=test123"
   ```

#### Erreur 403 : Signature invalide

```
{"detail": "Invalid signature"}
```

**Causes possibles :**
1. **URL webhook incorrecte dans la validation**
   - L'URL utilisée pour valider doit correspondre exactement à celle configurée dans Twilio
   
2. **Auth Token incorrect**
   - Vérifiez `TWILIO_AUTH_TOKEN` dans `.env`

3. **Payload modifié en transit**
   - Vérifiez qu'aucun proxy ne modifie les requêtes

**Solution temporaire pour les tests :**
```python
# Dans webhooks.py, désactiver temporairement la validation (DEV ONLY!)
# NE PAS FAIRE EN PRODUCTION
# if not twilio_service.validate_webhook_signature(url, params, signature):
#     raise HTTPException(status_code=403, detail="Invalid signature")
```

#### Webhooks reçus mais non traités

**Vérifiez les logs backend :**
```powershell
# Les logs doivent montrer le traitement du webhook
# Cherchez des erreurs dans la console du backend
```

**Vérifiez l'interface ngrok :**
- Ouvrez http://127.0.0.1:4040
- Inspectez les requêtes entrantes
- Vérifiez le code de réponse (doit être 200)

---

### 8.8 Erreurs de Base de Données

#### Tables manquantes

```
relation "contacts" does not exist
```

**Solution :**
1. Allez dans Supabase Dashboard > SQL Editor
2. Exécutez le script `database/schema.sql`
3. Exécutez `database/seed_superadmin.sql` pour créer l'admin

#### Erreur RLS (Row Level Security)

```
new row violates row-level security policy
```

**Solutions :**
1. Vérifiez que vous utilisez la clé `service_role` pour les opérations backend
2. Ou désactivez temporairement RLS pour les tests :
   ```sql
   ALTER TABLE contacts DISABLE ROW LEVEL SECURITY;
   ```

---

### 8.9 Erreurs d'Authentification

#### Token JWT invalide ou expiré

```
{"detail": "Could not validate credentials"}
```

**Solutions :**
1. Reconnectez-vous au dashboard
2. Vérifiez `SECRET_KEY` dans `.env`
3. Augmentez `ACCESS_TOKEN_EXPIRE_MINUTES` si nécessaire

#### Mot de passe incorrect

```
{"detail": "Incorrect email or password"}
```

**Solution :**
1. Vérifiez les credentials dans la base de données
2. Réinitialisez le mot de passe admin :
   ```sql
   -- Dans Supabase SQL Editor
   UPDATE users SET password_hash = '$2b$12$...' WHERE email = 'admin@chatbot.local';
   ```

---

### 8.10 Commandes de Diagnostic Utiles

```powershell
# === Vérification des ports ===
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# === Test de connectivité ===
Test-NetConnection -ComputerName localhost -Port 8000
Test-NetConnection -ComputerName localhost -Port 3000

# === Vérification des processus ===
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
Get-Process | Where-Object {$_.ProcessName -like "*node*"}
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}

# === Test API backend ===
curl http://localhost:8000/api/health
curl http://localhost:8000/api/docs

# === Vérification des variables d'environnement ===
cd backend
python -c "from app.config import settings; print(settings.TWILIO_ACCOUNT_SID[:10])"

# === Logs en temps réel ===
# Backend : les logs s'affichent dans le terminal où uvicorn est lancé
# ngrok : ouvrez http://127.0.0.1:4040 pour voir les requêtes

# === Nettoyage complet ===
# Backend
cd backend
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .pytest_cache -ErrorAction SilentlyContinue

# Frontend
cd frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
```

---

### 8.11 Tableau Récapitulatif des Erreurs Courantes

| Erreur | Cause | Solution Rapide |
|--------|-------|-----------------|
| `CORS policy blocked` | ALLOWED_ORIGINS mal configuré | Ajouter l'origine dans `.env` |
| `Network Error` | Backend non lancé | Lancer le backend |
| `Port already in use` | Processus existant | `taskkill /PID <PID> /F` |
| `Module not found` | Dépendances manquantes | `pip install -r requirements.txt` |
| `Invalid API key` | Clés Supabase incorrectes | Vérifier dans Supabase Dashboard |
| `63007` | Non inscrit au Sandbox | Envoyer `join <code>` |
| `20003` | Auth Token incorrect | Vérifier dans Twilio Console |
| `Invalid signature` | URL webhook incorrecte | Vérifier URL dans Twilio |
| `Connection refused` | Service non démarré | Démarrer le service concerné |
| `Token expired` | Session expirée | Se reconnecter |

---

## 📝 Checklist de Lancement

Utilisez cette checklist pour vérifier votre configuration :

### Prérequis
- [ ] Python 3.10+ installé
- [ ] Node.js 18+ installé
- [ ] Compte Supabase créé
- [ ] Compte Twilio créé
- [ ] Compte ngrok créé

### Configuration
- [ ] Tables créées dans Supabase (schema.sql)
- [ ] Utilisateur admin créé (seed_superadmin.sql)
- [ ] `backend/.env` configuré
- [ ] `frontend/.env.local` configuré
- [ ] ngrok authtoken configuré

### Démarrage
- [ ] Backend lancé (port 8000)
- [ ] ngrok lancé et URL notée
- [ ] Webhooks configurés dans Twilio
- [ ] Frontend lancé (port 3000)

### Tests
- [ ] Numéro de test inscrit au Sandbox Twilio
- [ ] Contact de test créé dans le dashboard
- [ ] Test d'envoi de message réussi
- [ ] Test de réception de webhook réussi

---

## 🎉 Félicitations !

Votre projet est maintenant configuré et fonctionnel en local. Vous pouvez :

- ✅ Créer des contacts et des catégories
- ✅ Lancer des campagnes WhatsApp via Twilio Sandbox
- ✅ Recevoir les réponses des clients
- ✅ Suivre les statuts de livraison

### Ressources Complémentaires

- [Configuration Twilio WhatsApp Sandbox](Configuration_Twilio_WhatsApp_Sandbox_2025.md)
- [Documentation API Twilio](https://www.twilio.com/docs/whatsapp)
- [Documentation Supabase](https://supabase.com/docs)
- [Documentation Next.js](https://nextjs.org/docs)

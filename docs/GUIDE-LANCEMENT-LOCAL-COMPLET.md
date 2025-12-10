# 🚀 Guide Complet - Lancement et Test du Projet en Local

> ⚠️ **OBSOLÈTE** : Ce guide contient des références à l'intégration Gupshup qui a été remplacée par Twilio WhatsApp Sandbox.
> 
> 📖 **Nouveau guide** : Consultez [Guide_Configuration_Projet_Local_2025.md](Guide_Configuration_Projet_Local_2025.md) pour la configuration avec Twilio WhatsApp Sandbox.
> 
> 📅 Date de migration : Décembre 2025

Ce guide vous accompagne pas à pas pour lancer le projet Chatbot WhatsApp en local et configurer l'intégration Gupshup avec les webhooks.

---

## 📋 Table des Matières

1. [Prérequis](#1-prérequis)
2. [Installation des Dépendances](#2-installation-des-dépendances)
3. [Configuration de Supabase](#3-configuration-de-supabase)
4. [Configuration du Backend](#4-configuration-du-backend)
5. [Configuration du Frontend](#5-configuration-du-frontend)
6. [Lancement du Projet](#6-lancement-du-projet)
7. [Configuration de ngrok (Tunnel HTTPS)](#7-configuration-de-ngrok-tunnel-https)
8. [Configuration du Webhook Gupshup](#8-configuration-du-webhook-gupshup)
9. [Test de l'Intégration](#9-test-de-lintégration)
10. [Dépannage](#10-dépannage)

---

## 1. Prérequis

### Logiciels Requis

| Logiciel | Version Minimum | Vérification |
|----------|-----------------|--------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | 2.0+ | `git --version` |

### Comptes Requis

- ✅ **Compte Supabase** : [supabase.com](https://supabase.com) (gratuit)
- ✅ **Compte Gupshup** : [gupshup.io](https://www.gupshup.io) (avec application WhatsApp active)
- ✅ **Compte ngrok** : [ngrok.com](https://ngrok.com) (gratuit, pour les webhooks en local)

---

## 2. Installation des Dépendances

### 2.1 Cloner le Projet (si pas déjà fait)

```bash
git clone <url-du-repo>
cd projet-chatbot-whatsapp
```

### 2.2 Installer les Dépendances Backend

```bash
cd backend

# Créer un environnement virtuel (recommandé)
python -m venv venv

# Activer l'environnement virtuel
# Windows :
venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2.3 Installer les Dépendances Frontend

```bash
cd frontend
npm install
```

---

## 3. Configuration de Supabase

### 3.1 Créer un Projet Supabase

1. Connectez-vous à [Supabase Dashboard](https://app.supabase.com)
2. Cliquez sur **New Project**
3. Remplissez les informations :
   - **Name** : `chatbot-whatsapp`
   - **Database Password** : Notez ce mot de passe !
   - **Region** : Choisissez la plus proche de vous
4. Cliquez sur **Create new project**

### 3.2 Récupérer les Clés API

1. Dans votre projet Supabase, allez dans **Settings** > **API**
2. Notez les informations suivantes :

| Information | Où la trouver | Exemple |
|-------------|---------------|---------|
| **Project URL** | Section "Project URL" | `https://abc123.supabase.co` |
| **anon public** | Section "Project API keys" | `eyJhbGciOiJIUzI1NiIs...` |
| **service_role** | Section "Project API keys" (cliquez sur "Reveal") | `eyJhbGciOiJIUzI1NiIs...` |

### 3.3 Créer les Tables

1. Allez dans **SQL Editor** dans Supabase
2. Copiez et exécutez le contenu du fichier `database/schema.sql`
3. Puis exécutez `database/seed_superadmin.sql` pour créer l'utilisateur admin

---

## 4. Configuration du Backend

### 4.1 Créer le Fichier .env

```bash
cd backend
copy .env.example .env
```

### 4.2 Configurer les Variables

Ouvrez `backend/.env` et modifiez les valeurs suivantes :

```env
# =============================================================================
# ENVIRONNEMENT
# =============================================================================
ENVIRONMENT=development
DEBUG=True

# =============================================================================
# SUPABASE (Remplacez par vos valeurs)
# =============================================================================
SUPABASE_URL=https://VOTRE_PROJECT_ID.supabase.co
SUPABASE_KEY=votre_anon_key_ici
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key_ici
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@db.VOTRE_PROJECT_ID.supabase.co:5432/postgres

# =============================================================================
# GUPSHUP API (2025)
# =============================================================================
# Clé API Gupshup (trouvée dans Gupshup Dashboard > Settings > API Keys)
GUPSHUP_API_KEY=votre_cle_api_gupshup

# Nom de l'application (visible dans Gupshup Dashboard)
GUPSHUP_APP_NAME=newsteck

# Numéro WhatsApp SANS le + (ex: 33753117215)
GUPSHUP_PHONE_NUMBER=33753117215

# URL de l'API Gupshup (ne pas modifier)
GUPSHUP_API_URL=https://api.gupshup.io/sm/api/v1

# ID Client (optionnel)
GUPSHUP_CUSTOMER_ID=4000322028

# =============================================================================
# AUTHENTIFICATION JWT
# =============================================================================
# Générez une clé secrète unique :
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=votre_cle_secrete_generee_ici

# =============================================================================
# REDIS (optionnel pour Celery)
# =============================================================================
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# CORS
# =============================================================================
ALLOWED_ORIGINS=http://localhost:3000
```

### 4.3 Vérifier la Configuration

```bash
cd backend
python -c "
from app.config import settings
print('=== Configuration Backend ===')
print(f'Supabase URL: {settings.SUPABASE_URL}')
print(f'Gupshup App: {settings.GUPSHUP_APP_NAME}')
print(f'Gupshup Phone: {settings.GUPSHUP_PHONE_NUMBER}')
print('✅ Configuration OK!')
"
```

---

## 5. Configuration du Frontend

### 5.1 Créer le Fichier .env.local

```bash
cd frontend
copy .env.local.example .env.local
```

### 5.2 Configurer les Variables

Ouvrez `frontend/.env.local` et modifiez :

```env
# URL de l'API Backend
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Supabase (mêmes valeurs que le backend)
NEXT_PUBLIC_SUPABASE_URL=https://VOTRE_PROJECT_ID.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_anon_key_ici
```

---

## 6. Lancement du Projet

### 6.1 Lancer le Backend

**Option A : Script automatique (Windows)**
```bash
# Double-cliquez sur start_backend.bat à la racine du projet
```

**Option B : Manuellement**
```bash
cd backend

# Activer l'environnement virtuel si nécessaire
venv\Scripts\activate

# Lancer le serveur
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ Le backend est accessible sur :
- **API** : http://localhost:8000
- **Documentation Swagger** : http://localhost:8000/api/docs
- **Health Check** : http://localhost:8000/api/health

### 6.2 Lancer le Frontend

**Option A : Script automatique (Windows)**
```bash
# Double-cliquez sur start_frontend.bat à la racine du projet
```

**Option B : Manuellement**
```bash
cd frontend
npm run dev
```

✅ Le frontend est accessible sur : http://localhost:3000

### 6.3 Se Connecter à l'Application

Ouvrez http://localhost:3000 et connectez-vous avec :

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Super Admin | `superadmin@chatbot.local` | `SuperAdmin2024!` |
| Admin | `admin@chatbot.local` | `Admin2024!` |

---

## 7. Configuration de ngrok (Tunnel HTTPS)

Pour recevoir les webhooks Gupshup en local, vous devez exposer votre backend via HTTPS. ngrok crée un tunnel sécurisé.

### 7.1 Installer ngrok

1. Téléchargez ngrok : https://ngrok.com/download
2. Extrayez l'archive
3. Ajoutez ngrok à votre PATH ou placez-le dans un dossier accessible

### 7.2 Créer un Compte ngrok (Gratuit)

1. Inscrivez-vous sur https://ngrok.com
2. Récupérez votre **Authtoken** dans le dashboard ngrok
3. Configurez ngrok :

```bash
ngrok config add-authtoken VOTRE_AUTHTOKEN
```

### 7.3 Lancer ngrok

**Assurez-vous que le backend est lancé sur le port 8000**, puis :

```bash
ngrok http 8000
```

Vous verrez quelque chose comme :

```
Session Status                online
Account                       votre@email.com
Version                       3.x.x
Region                        Europe (eu)
Forwarding                    https://abc123xyz.ngrok-free.app -> http://localhost:8000
```

📝 **Notez l'URL HTTPS** (ex: `https://abc123xyz.ngrok-free.app`)

Cette URL change à chaque redémarrage de ngrok (sauf avec un compte payant).

---

## 8. Configuration du Webhook Gupshup

### 8.1 Accéder au Dashboard Gupshup

1. Connectez-vous à https://www.gupshup.io/developer/home
2. Cliquez sur **WhatsApp** dans le menu
3. Sélectionnez votre application **newsteck**
4. Allez dans l'onglet **Settings**

### 8.2 Configurer le Webhook

Dans la section **Configure Webhook**, cliquez sur **Add Webhook**.

Remplissez le formulaire comme suit :

| Champ | Valeur |
|-------|--------|
| **Webhook Name (Tag)** | `chatbot-local` |
| **Callback URL** | `https://VOTRE_URL_NGROK/api/webhooks/gupshup` |

**Exemple de Callback URL :**
```
https://abc123xyz.ngrok-free.app/api/webhooks/gupshup
```

### 8.3 Sélectionner le Format de Payload

⚠️ **IMPORTANT** : Sélectionnez **Gupshup format (v2)** (pas Meta format v3)

Notre service est conçu pour le format Gupshup natif.

### 8.4 Sélectionner les Événements

Cochez les événements suivants :

**Message Events :**
- ✅ **Message** - Pour recevoir les messages des clients
- ✅ **Sent** - Pour savoir quand un message est envoyé
- ✅ **Delivered** - Pour savoir quand un message est délivré
- ✅ **Read** - Pour savoir quand un message est lu
- ✅ **Failed** - Pour savoir quand un message échoue

**System Events :**
- ✅ **Template events** - Pour les notifications de templates

### 8.5 Sauvegarder

Cliquez sur **Add Webhook** pour sauvegarder la configuration.

### 8.6 Récapitulatif de la Configuration

```
┌─────────────────────────────────────────────────────────────┐
│                    ADD WEBHOOK                               │
├─────────────────────────────────────────────────────────────┤
│ Webhook Name (Tag): chatbot-local                           │
│                                                             │
│ Callback URL: https://abc123xyz.ngrok-free.app/api/webhooks/gupshup │
│                                                             │
│ Payload Format: ○ Gupshup format (v2) ← SÉLECTIONNER        │
│                 ○ Meta format (v3)                          │
│                                                             │
│ Message Events:                                             │
│   ☑ Message    ☐ Enqueued    ☑ Failed                      │
│   ☑ Sent       ☑ Delivered   ☑ Read                        │
│   ☐ Delete     ☐ Billing     ☐ Flow Message                │
│   ☐ Payments   ☐ Others                                    │
│                                                             │
│ System Events:                                              │
│   ☑ Template events    ☐ Account related events            │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Test de l'Intégration

### 9.1 Vérifier que le Backend Reçoit les Webhooks

1. Gardez un œil sur les logs du backend (terminal où uvicorn tourne)
2. Envoyez un message WhatsApp vers votre numéro Business (+33 7 53 11 72 15)
3. Vous devriez voir dans les logs :

```
INFO - Webhook Gupshup reçu: type=message
INFO - Webhook Gupshup parsé: 1 interaction(s) extraite(s)
```

### 9.2 Tester l'Envoi d'un Message

#### Via l'Interface Web

1. Connectez-vous au dashboard (http://localhost:3000)
2. Allez dans **Contacts** et ajoutez un contact avec votre numéro WhatsApp
3. Allez dans **Campagnes** et créez une nouvelle campagne
4. Sélectionnez un template approuvé sur Gupshup
5. Lancez la campagne

#### Via l'API (curl)

```bash
# Tester l'envoi d'un message template
curl -X POST "https://api.gupshup.io/sm/api/v1/template/msg" \
  -H "apikey: VOTRE_API_KEY" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "channel=whatsapp" \
  -d "source=33753117215" \
  -d "destination=VOTRE_NUMERO_SANS_PLUS" \
  -d 'template={"id":"hello_world","params":[]}' \
  -d "src.name=newsteck"
```

### 9.3 Vérifier le Flux Complet

1. **Message 1** : Envoyez une campagne avec un template
2. **Webhook Statut** : Vérifiez que le statut passe à "delivered" puis "read"
3. **Réponse Client** : Répondez au message depuis WhatsApp
4. **Message 2** : Vérifiez que le Message 2 automatique est envoyé

### 9.4 Vérifier les Logs ngrok

ngrok affiche toutes les requêtes reçues. Vous pouvez aussi accéder à l'interface web :

```
http://127.0.0.1:4040
```

Cette interface montre :
- Toutes les requêtes HTTP reçues
- Les payloads des webhooks
- Les réponses de votre backend

---

## 10. Dépannage

### Le Backend ne Démarre Pas

**Erreur : Module not found**
```bash
pip install -r requirements.txt
```

**Erreur : Variables d'environnement manquantes**
```bash
# Vérifiez que .env existe et contient toutes les variables
cat backend/.env
```

### Le Frontend ne Démarre Pas

**Erreur : npm packages manquants**
```bash
cd frontend
rm -rf node_modules
npm install
```

### ngrok ne Fonctionne Pas

**Erreur : Authtoken invalide**
```bash
ngrok config add-authtoken VOTRE_NOUVEAU_TOKEN
```

**L'URL change à chaque redémarrage**
- C'est normal avec le plan gratuit
- Mettez à jour l'URL dans Gupshup Dashboard à chaque fois
- Ou passez à un plan payant pour une URL fixe

### Les Webhooks ne Sont Pas Reçus

1. **Vérifiez l'URL** : L'URL dans Gupshup doit correspondre exactement à votre URL ngrok + `/api/webhooks/gupshup`

2. **Vérifiez le format** : Assurez-vous d'avoir sélectionné **Gupshup format (v2)**

3. **Vérifiez les événements** : Les cases Message, Delivered, Read doivent être cochées

4. **Testez l'endpoint manuellement** :
```bash
curl -X POST "https://VOTRE_URL_NGROK/api/webhooks/gupshup" \
  -H "Content-Type: application/json" \
  -d '{"type":"message","mobile":"33612345678","text":"test","messageId":"test123"}'
```

### Erreur 401 sur Gupshup

- Vérifiez que `GUPSHUP_API_KEY` est correct dans `.env`
- Régénérez la clé API si nécessaire

### Les Messages ne Sont Pas Envoyés

1. Vérifiez que le template est approuvé sur Gupshup Dashboard
2. Vérifiez le format du numéro (sans le +)
3. Consultez les logs du backend pour les erreurs détaillées

---

## 📝 Checklist de Lancement

- [ ] Python 3.10+ installé
- [ ] Node.js 18+ installé
- [ ] Projet Supabase créé
- [ ] Tables créées dans Supabase
- [ ] `backend/.env` configuré
- [ ] `frontend/.env.local` configuré
- [ ] Backend lancé (port 8000)
- [ ] Frontend lancé (port 3000)
- [ ] ngrok lancé et URL notée
- [ ] Webhook configuré sur Gupshup Dashboard
- [ ] Test d'envoi de message réussi
- [ ] Test de réception de webhook réussi

---

## 🎉 Félicitations !

Votre projet est maintenant configuré et fonctionnel en local. Vous pouvez :

- Créer des contacts et des catégories
- Lancer des campagnes WhatsApp
- Recevoir les réponses des clients
- Envoyer automatiquement le Message 2

Pour le déploiement en production, consultez `docs/04-DEPLOIEMENT-GRATUIT.md`.

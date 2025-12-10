# 🚀 Guide de Lancement du Projet - Wassenger 2025

Ce guide vous accompagne pas à pas pour configurer et lancer le projet de chatbot WhatsApp avec l'intégration Wassenger 2025.

---

## 📋 Table des Matières

1. [Prérequis](#1-prérequis)
2. [Configuration Supabase](#2-configuration-supabase)
3. [Configuration Backend (.env)](#3-configuration-backend-env)
4. [Configuration Frontend (.env.local)](#4-configuration-frontend-envlocal)
5. [Lancement Local](#5-lancement-local)
6. [Configuration ngrok](#6-configuration-ngrok)
7. [Configuration Webhook Wassenger](#7-configuration-webhook-wassenger)
8. [Tests du Workflow](#8-tests-du-workflow)
9. [Dépannage](#9-dépannage)

---

## 1. Prérequis

### 🐍 Python 3.10+

```bash
# Vérifier la version de Python
python --version
# Doit afficher Python 3.10.x ou supérieur
```

**Installation Windows :**
- Téléchargez depuis [python.org](https://www.python.org/downloads/)
- Cochez "Add Python to PATH" lors de l'installation

### 📦 Node.js 18+

```bash
# Vérifier la version de Node.js
node --version
# Doit afficher v18.x.x ou supérieur

# Vérifier npm
npm --version
```

**Installation :**
- Téléchargez depuis [nodejs.org](https://nodejs.org/)

### 🔗 ngrok

ngrok permet d'exposer votre serveur local sur Internet pour recevoir les webhooks Wassenger.

```bash
# Vérifier si ngrok est installé
ngrok --version
```

**Installation :**
1. Créez un compte gratuit sur [ngrok.com](https://ngrok.com/)
2. Téléchargez ngrok pour votre système
3. Configurez votre authtoken :
```bash
ngrok config add-authtoken VOTRE_TOKEN
```

### 🗄️ Redis (optionnel pour Celery)

Redis est nécessaire pour les tâches asynchrones Celery.

**Windows :**
- Utilisez [Memurai](https://www.memurai.com/) (alternative Redis pour Windows)
- Ou Docker : `docker run -d -p 6379:6379 redis`

---

## 2. Configuration Supabase

### 2.1 Créer un Projet Supabase

1. Connectez-vous à [supabase.com](https://supabase.com/)
2. Cliquez sur **New Project**
3. Remplissez les informations :
   - **Name** : chatbot-whatsapp
   - **Database Password** : Générez un mot de passe fort
   - **Region** : Choisissez la plus proche de vos utilisateurs

### 2.2 Récupérer les Credentials

Dans le dashboard Supabase, allez dans **Settings > API** :

| Variable | Où la trouver |
|----------|---------------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_KEY` | anon public |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role (secret) |

Dans **Settings > Database > Connection string** :
| Variable | Où la trouver |
|----------|---------------|
| `DATABASE_URL` | URI (mode: Transaction) |

### 2.3 Exécuter le Schéma SQL

1. Allez dans **SQL Editor**
2. Copiez le contenu de `database/schema.sql`
3. Exécutez le script
4. Répétez pour `database/rls_policies.sql`
5. Exécutez `database/seed_admin.sql` pour créer l'utilisateur admin

---

## 3. Configuration Backend (.env)

### 3.1 Créer le Fichier .env

```bash
cd backend
copy .env.example .env
```

### 3.2 Configurer les Variables Obligatoires

Ouvrez `backend/.env` et remplissez :

```env
# =============================================================================
# SUPABASE
# =============================================================================
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_anon_key
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key
DATABASE_URL=postgresql://postgres:password@db.votre-projet.supabase.co:5432/postgres

# =============================================================================
# WASSENGER API 2025
# =============================================================================
WASSENGER_API_KEY=wsp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WASSENGER_DEVICE_ID=64a1b2c3d4e5f6g7h8i9j0k1
WASSENGER_WEBHOOK_URL=https://votre-url.ngrok.io/api/webhooks/wassenger

# =============================================================================
# JWT (Générez une clé secrète unique)
# =============================================================================
SECRET_KEY=votre_cle_secrete_minimum_32_caracteres
```

### 3.3 Générer une Clé Secrète JWT

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copiez le résultat dans `SECRET_KEY`.

---

## 4. Configuration Frontend (.env.local)

### 4.1 Créer le Fichier .env.local

```bash
cd frontend
copy .env.local.example .env.local
```

### 4.2 Configurer les Variables

```env
# URL de l'API Backend
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Supabase (mêmes valeurs que le backend)
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_anon_key
```

---

## 5. Lancement Local

### 5.1 Démarrer le Backend

**Terminal 1 :**

```bash
cd backend

# Créer l'environnement virtuel (première fois uniquement)
python -m venv venv

# Activer l'environnement virtuel
# Windows CMD :
venv\Scripts\activate
# Windows PowerShell :
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Le backend est accessible sur `http://localhost:8000`
✅ Documentation API : `http://localhost:8000/docs`

### 5.2 Démarrer le Frontend

**Terminal 2 :**

```bash
cd frontend

# Installer les dépendances (première fois uniquement)
npm install

# Lancer le serveur de développement
npm run dev
```

✅ Le frontend est accessible sur `http://localhost:3000`

### 5.3 Scripts de Lancement Rapide

Utilisez les scripts batch fournis :

```bash
# Lancer le backend
start_backend.bat

# Lancer le frontend
start_frontend.bat
```

---

## 6. Configuration ngrok

### 6.1 Démarrer ngrok

**Terminal 3 :**

```bash
ngrok http 8000
```

### 6.2 Récupérer l'URL Publique

ngrok affiche une URL comme :
```
Forwarding    https://abc123.ngrok.io -> http://localhost:8000
```

📝 **Notez cette URL** - vous en aurez besoin pour configurer le webhook Wassenger.

### 6.3 Mettre à Jour .env

Mettez à jour `WASSENGER_WEBHOOK_URL` dans `backend/.env` :

```env
WASSENGER_WEBHOOK_URL=https://abc123.ngrok.io/api/webhooks/wassenger
```

⚠️ **Important** : L'URL ngrok change à chaque redémarrage (sauf avec un compte payant).

---

## 7. Configuration Webhook Wassenger

### 7.1 Accéder au Dashboard Wassenger

1. Connectez-vous à [app.wassenger.com](https://app.wassenger.com/)
2. Allez dans **Settings > Webhooks**

### 7.2 Créer un Nouveau Webhook

1. Cliquez sur **Add Webhook**
2. Configurez :
   - **URL** : `https://votre-url.ngrok.io/api/webhooks/wassenger`
   - **Events** : Sélectionnez tous les événements :
     - ✅ `message:in:new` (messages entrants)
     - ✅ `message:out:sent` (messages envoyés)
     - ✅ `message:out:delivered` (messages délivrés)
     - ✅ `message:out:read` (messages lus)
     - ✅ `message:out:failed` (échecs d'envoi)
3. Cliquez sur **Save**

### 7.3 Tester le Webhook

1. Cliquez sur **Test** dans le dashboard Wassenger
2. Vérifiez dans les logs du backend que le webhook est reçu :
```
INFO: Webhook Wassenger reçu: message:in:new
```

---

## 8. Tests du Workflow

### 8.1 Test d'Envoi de Message

1. Connectez-vous au dashboard : `http://localhost:3000/login`
   - Email : `admin@example.com`
   - Mot de passe : (celui défini dans seed_admin.sql)

2. Créez un contact test :
   - Allez dans **Contacts > Nouveau Contact**
   - Entrez votre numéro WhatsApp (format : 22890123456)

3. Créez une campagne :
   - Allez dans **Campagnes > Nouvelle Campagne**
   - Sélectionnez le contact
   - Rédigez le Message 1
   - Lancez la campagne

4. Vérifiez :
   - ✅ Le message apparaît dans WhatsApp
   - ✅ Le statut passe à "sent" puis "delivered"

### 8.2 Test du Workflow Message 2

1. Répondez au Message 1 depuis WhatsApp
2. Vérifiez dans le dashboard :
   - ✅ L'interaction est enregistrée
   - ✅ Le Message 2 est envoyé automatiquement
   - ✅ Les statistiques sont mises à jour

### 8.3 Vérifier les Logs

```bash
# Dans le terminal du backend, vous devriez voir :
INFO: Message envoyé avec succès: msg_abc123
INFO: Webhook Wassenger reçu: message:out:delivered
INFO: Webhook Wassenger reçu: message:in:new
INFO: Message 2 programmé pour le contact: 22890123456
```

---

## 9. Dépannage

### ❌ Erreur "WASSENGER_API_KEY manquante"

**Cause** : La variable d'environnement n'est pas définie.

**Solution** :
1. Vérifiez que le fichier `.env` existe dans `backend/`
2. Vérifiez que `WASSENGER_API_KEY` est définie et non vide
3. Redémarrez le serveur backend

### ❌ Erreur "device_not_connected"

**Cause** : L'appareil WhatsApp n'est pas connecté à Wassenger.

**Solution** :
1. Allez dans le dashboard Wassenger > Devices
2. Scannez le QR code avec WhatsApp
3. Attendez que le statut passe à "Connected"

### ❌ Webhook non reçu

**Causes possibles** :
- ngrok n'est pas démarré
- L'URL du webhook est incorrecte
- Le pare-feu bloque les connexions

**Solutions** :
1. Vérifiez que ngrok est actif : `ngrok http 8000`
2. Testez l'URL dans un navigateur : `https://votre-url.ngrok.io/docs`
3. Vérifiez l'URL dans le dashboard Wassenger

### ❌ Erreur "invalid_phone_number"

**Cause** : Le format du numéro est incorrect.

**Solution** :
- Utilisez le format international sans le + : `22890123456`
- Ne pas inclure d'espaces ou de tirets

### ❌ Erreur de connexion Supabase

**Causes possibles** :
- URL ou clés incorrectes
- Projet Supabase en pause

**Solutions** :
1. Vérifiez les credentials dans `.env`
2. Allez dans le dashboard Supabase et vérifiez que le projet est actif
3. Si le projet est en pause, cliquez sur "Resume project"

### ❌ Le frontend ne se connecte pas au backend

**Causes possibles** :
- CORS non configuré
- Backend non démarré

**Solutions** :
1. Vérifiez que le backend est accessible : `http://localhost:8000/docs`
2. Vérifiez `ALLOWED_ORIGINS` dans `.env` : `http://localhost:3000`
3. Redémarrez le backend

### ❌ Messages non envoyés (rate limit)

**Cause** : Trop de messages envoyés trop rapidement.

**Solution** :
- Le système attend automatiquement 2 secondes entre chaque message
- Si l'erreur persiste, attendez 60 secondes avant de réessayer

---

## 📞 Support

Si vous rencontrez des problèmes non résolus par ce guide :

1. Consultez les logs du backend pour plus de détails
2. Vérifiez la documentation Wassenger : [wassenger.com/docs](https://wassenger.com/docs)
3. Consultez les autres guides dans le dossier `docs/`

celery: celery -A app.tasks.celery_app worker --loglevel=info --pool=solo


---

*Guide mis à jour : Décembre 2025*

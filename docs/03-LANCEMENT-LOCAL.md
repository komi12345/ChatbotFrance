# 🚀 Lancement Local du Projet

Ce guide explique comment lancer le projet en local pour le développement.

## Prérequis

- **Python 3.10+** installé
- **Node.js 18+** installé
- **Compte Supabase** configuré (voir `01-CONFIGURATION.md`)

## 1. Configuration des Variables d'Environnement

### Backend (`backend/.env`)

Copiez le fichier exemple et configurez vos variables :

```bash
cd backend
cp .env.example .env
```

Variables importantes :
- `SUPABASE_URL` : URL de votre projet Supabase
- `SUPABASE_KEY` : Clé publique (anon key)
- `SUPABASE_SERVICE_ROLE_KEY` : Clé de service (côté serveur uniquement)
- `SECRET_KEY` : Clé secrète pour JWT (générez-en une unique)

### Frontend (`frontend/.env.local`)

```bash
cd frontend
cp .env.local.example .env.local
```

Variables importantes :
- `NEXT_PUBLIC_API_URL` : URL de l'API backend (http://localhost:8000/api)
- `NEXT_PUBLIC_SUPABASE_URL` : URL Supabase
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` : Clé publique Supabase

## 2. Lancement du Backend

### Option 1 : Script automatique (Windows)

Double-cliquez sur `start_backend.bat` à la racine du projet.

### Option 2 : Manuellement

```bash
cd backend

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Le backend sera accessible sur :
- **API** : http://localhost:8000
- **Documentation Swagger** : http://localhost:8000/api/docs
- **Health Check** : http://localhost:8000/api/health

## 3. Lancement du Frontend

### Option 1 : Script automatique (Windows)

Double-cliquez sur `start_frontend.bat` à la racine du projet.

### Option 2 : Manuellement

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

Le frontend sera accessible sur : http://localhost:3000

## 4. Connexion à l'Application

Utilisez les identifiants par défaut :

**Super Admin :**
- Email : `superadmin@chatbot.local`
- Mot de passe : `SuperAdmin2024!`

**Admin :**
- Email : `admin@chatbot.local`
- Mot de passe : `Admin2024!`

## 5. Architecture Technique

### Backend (FastAPI + Supabase)

Le backend utilise :
- **FastAPI** : Framework web Python moderne
- **Supabase Client** : Connexion à la base de données via API REST
- **JWT** : Authentification par tokens

Avantages de l'architecture Supabase :
- ✅ Pas de connexion PostgreSQL directe (évite les problèmes de firewall)
- ✅ Fonctionne partout (local, cloud, derrière NAT)
- ✅ Scalable automatiquement
- ✅ Sécurisé avec Row Level Security (RLS)

### Frontend (Next.js)

Le frontend utilise :
- **Next.js 14** : Framework React avec App Router
- **TailwindCSS** : Styling utilitaire
- **React Query** : Gestion du cache et des requêtes
- **Shadcn/ui** : Composants UI

## 6. Dépannage

### Le backend ne démarre pas

1. Vérifiez que Python 3.10+ est installé : `python --version`
2. Vérifiez que les dépendances sont installées : `pip install -r requirements.txt`
3. Vérifiez le fichier `.env` dans le dossier `backend`

### Le frontend ne démarre pas

1. Vérifiez que Node.js 18+ est installé : `node --version`
2. Supprimez `node_modules` et réinstallez : `rm -rf node_modules && npm install`
3. Vérifiez le fichier `.env.local` dans le dossier `frontend`

### Erreur de connexion à Supabase

1. Vérifiez que votre projet Supabase est actif (pas en pause)
2. Vérifiez les clés API dans les fichiers `.env`
3. Testez la connexion : `python backend/test_supabase_client.py`

### Erreur CORS

Vérifiez que `ALLOWED_ORIGINS` dans `backend/.env` inclut `http://localhost:3000`

## 7. Commandes Utiles

```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload  # Démarrer avec hot-reload

# Frontend
cd frontend
npm run dev      # Démarrer en développement
npm run build    # Build de production
npm run lint     # Vérifier le code
```

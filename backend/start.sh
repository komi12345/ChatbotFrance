#!/bin/bash
# Script de démarrage pour Render - Lance Celery et Uvicorn ensemble
# Ce script est plus robuste que le Procfile simple

set -e

echo "=== Démarrage du backend WhatsApp Chatbot ==="
echo "PORT: ${PORT:-8000}"
echo "ENVIRONMENT: ${ENVIRONMENT:-development}"

# Fonction pour arrêter proprement les processus
cleanup() {
    echo "Arrêt des processus..."
    kill $CELERY_PID 2>/dev/null || true
    kill $UVICORN_PID 2>/dev/null || true
    exit 0
}

# Capturer les signaux d'arrêt
trap cleanup SIGTERM SIGINT

# Démarrer Celery Worker en arrière-plan
echo "Démarrage de Celery Worker..."
celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    -Q default,messages,messages_high,retry,verification \
    2>&1 | sed 's/^/[CELERY] /' &
CELERY_PID=$!
echo "Celery Worker démarré (PID: $CELERY_PID)"

# Attendre un peu que Celery démarre
sleep 3

# Vérifier que Celery est bien démarré
if ! kill -0 $CELERY_PID 2>/dev/null; then
    echo "ERREUR: Celery n'a pas démarré correctement"
    exit 1
fi

# Démarrer Uvicorn (FastAPI) au premier plan
echo "Démarrage de Uvicorn (FastAPI)..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --log-level info &
UVICORN_PID=$!
echo "Uvicorn démarré (PID: $UVICORN_PID)"

# Attendre que l'un des processus se termine
wait -n $CELERY_PID $UVICORN_PID

# Si on arrive ici, un processus s'est arrêté
echo "Un processus s'est arrêté, arrêt du service..."
cleanup

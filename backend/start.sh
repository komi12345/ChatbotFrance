#!/bin/bash
# Script de démarrage pour Render - Lance Celery et Uvicorn ensemble
# Ce script est plus robuste que le Procfile simple

echo "=== Démarrage du backend WhatsApp Chatbot ==="
echo "PORT: ${PORT:-8000}"
echo "ENVIRONMENT: ${ENVIRONMENT:-development}"

# Fonction pour arrêter proprement les processus
cleanup() {
    echo "Arrêt des processus..."
    if [ ! -z "$CELERY_PID" ]; then
        kill $CELERY_PID 2>/dev/null || true
    fi
    kill $UVICORN_PID 2>/dev/null || true
    exit 0
}

# Capturer les signaux d'arrêt
trap cleanup SIGTERM SIGINT

# Vérifier si REDIS_URL est configuré
if [ -z "$REDIS_URL" ]; then
    echo "⚠️  REDIS_URL non configuré - Celery ne sera pas démarré"
    echo "⚠️  L'envoi de messages en masse ne fonctionnera pas"
    echo "⚠️  Configurez REDIS_URL sur Render pour activer Celery"
    CELERY_ENABLED=false
else
    echo "✅ REDIS_URL configuré - Celery sera démarré"
    CELERY_ENABLED=true
fi

# Démarrer Celery Worker si Redis est configuré
if [ "$CELERY_ENABLED" = true ]; then
    echo "Démarrage de Celery Worker..."
    celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --concurrency=1 \
        -Q default,messages,messages_high,retry,verification \
        2>&1 | sed 's/^/[CELERY] /' &
    CELERY_PID=$!
    echo "Celery Worker démarré (PID: $CELERY_PID)"
    
    # Attendre un peu que Celery démarre
    sleep 5
    
    # Vérifier que Celery est bien démarré
    if ! kill -0 $CELERY_PID 2>/dev/null; then
        echo "⚠️  Celery n'a pas démarré correctement, continuation sans Celery..."
        CELERY_ENABLED=false
    fi
fi

# Démarrer Uvicorn (FastAPI)
echo "Démarrage de Uvicorn (FastAPI)..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --log-level info &
UVICORN_PID=$!
echo "Uvicorn démarré (PID: $UVICORN_PID)"

# Attendre les processus
if [ "$CELERY_ENABLED" = true ]; then
    # Attendre que l'un des processus se termine
    wait $UVICORN_PID
else
    # Attendre seulement Uvicorn
    wait $UVICORN_PID
fi

# Si on arrive ici, un processus s'est arrêté
echo "Un processus s'est arrêté, arrêt du service..."
cleanup

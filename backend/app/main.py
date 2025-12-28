"""
Point d'entrée principal de l'application FastAPI
Chatbot WhatsApp - Backend API
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings, validate_config_on_startup
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.contacts import router as contacts_router
from app.routers.webhooks import router as webhooks_router
from app.routers.campaigns import router as campaigns_router
from app.routers.messages import router as messages_router
from app.routers.users import router as users_router
from app.routers.verify import router as verify_router
from app.routers.monitoring import router as monitoring_router
from app.routers.cache import router as cache_router

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    logger.info(f"Démarrage de l'application en mode {settings.ENVIRONMENT}")
    logger.info(f"CORS autorisé pour: {settings.allowed_origins_list}")
    
    # Validation de la configuration Wassenger au démarrage
    try:
        validate_config_on_startup()
        logger.info("Configuration Wassenger validée avec succès")
    except ValueError as e:
        logger.error(str(e))
        # En mode développement, on continue malgré l'erreur pour permettre les tests
        if settings.ENVIRONMENT == "production":
            raise
        else:
            logger.warning("Mode développement : l'application continue malgré la configuration Wassenger incomplète")
    
    yield
    # Shutdown
    logger.info("Arrêt de l'application")


# Création de l'application FastAPI
app = FastAPI(
    title="Chatbot WhatsApp API",
    description="API REST pour le système de chatbot WhatsApp avec dashboard d'administration",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Capture toutes les exceptions non gérées"""
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Une erreur interne s'est produite",
            "error": str(exc) if settings.DEBUG else "Internal Server Error"
        }
    )


# Route de santé (GET et HEAD pour UptimeRobot)
@app.get("/api/health", tags=["Health"])
@app.head("/api/health", tags=["Health"])
async def health_check():
    """Vérifie que l'API est opérationnelle"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


# Inclusion des routers
app.include_router(auth_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(verify_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(cache_router, prefix="/api")


# Route racine
@app.get("/", tags=["Root"])
async def root():
    """Route racine de l'API"""
    return {
        "message": "Bienvenue sur l'API Chatbot WhatsApp",
        "docs": "/api/docs" if settings.DEBUG else "Documentation désactivée en production"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

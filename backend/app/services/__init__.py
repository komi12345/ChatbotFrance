# Services métier
# Les imports sont faits directement là où ils sont nécessaires pour éviter les imports circulaires

# Wassenger WhatsApp API (2025) - Nouvelle intégration
from app.services.wassenger_service import (
    wassenger_service,
    WassengerService,
    WassengerResponse,
    WassengerWebhookInteraction,
)

__all__ = [
    # Wassenger (nouvelle intégration 2025)
    "wassenger_service",
    "WassengerService",
    "WassengerResponse",
    "WassengerWebhookInteraction",
]

"""
Tâches Celery - Module d'initialisation
Exporte l'application Celery et les tâches de messages
"""
from app.tasks.celery_app import celery_app, rate_limiter, get_celery_app
from app.tasks.message_tasks import (
    send_single_message,
    send_campaign_messages,
    retry_failed_message,
    retry_campaign_failed_messages,
    update_campaign_status,
)

__all__ = [
    "celery_app",
    "rate_limiter",
    "get_celery_app",
    "send_single_message",
    "send_campaign_messages",
    "retry_failed_message",
    "retry_campaign_failed_messages",
    "update_campaign_status",
]

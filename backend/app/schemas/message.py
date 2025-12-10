"""
Schémas Pydantic pour les messages
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Schéma de réponse pour un message"""
    id: int
    campaign_id: int
    contact_id: int
    message_type: str
    content: str
    status: str
    whatsapp_message_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageContactInfo(BaseModel):
    """Informations du contact pour un message"""
    id: int
    phone_number: str
    full_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class MessageCampaignInfo(BaseModel):
    """Informations de la campagne pour un message"""
    id: int
    name: str


class MessageWithContact(MessageResponse):
    """Schéma de message avec les informations du contact et de la campagne"""
    contact_full_number: str
    contact_name: Optional[str] = None
    campaign_name: Optional[str] = None
    # Objets imbriqués pour compatibilité frontend
    contact: Optional[MessageContactInfo] = None
    campaign: Optional[MessageCampaignInfo] = None


class MessageStats(BaseModel):
    """Schéma pour les statistiques globales des messages"""
    total_messages: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    pending_count: int
    success_rate: float
    delivery_rate: float
    read_rate: float


class MessageDailyStats(BaseModel):
    """Schéma pour les statistiques quotidiennes"""
    date: str
    sent: int
    delivered: int
    read: int
    failed: int


class MessageFilter(BaseModel):
    """Schéma pour les filtres de recherche de messages"""
    campaign_id: Optional[int] = None
    contact_id: Optional[int] = None
    status: Optional[str] = None
    message_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class InteractionResponse(BaseModel):
    """Schéma de réponse pour une interaction"""
    id: int
    campaign_id: int
    contact_id: int
    message_id: Optional[int] = None
    interaction_type: str
    content: Optional[str] = None
    whatsapp_message_id: Optional[str] = None
    received_at: datetime
    
    class Config:
        from_attributes = True


class InteractionWithDetails(InteractionResponse):
    """Schéma d'interaction avec détails du contact"""
    contact_full_number: str
    contact_name: Optional[str] = None

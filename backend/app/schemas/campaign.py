"""
Schémas Pydantic pour les campagnes
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re


class CampaignBase(BaseModel):
    """Schéma de base pour les campagnes"""
    name: str = Field(..., min_length=1, max_length=255)
    message_1: str = Field(..., min_length=1)
    message_2: Optional[str] = None
    template_name: Optional[str] = Field(None, max_length=100)


class CampaignCreate(CampaignBase):
    """Schéma pour la création d'une campagne"""
    category_ids: List[int] = Field(..., min_length=1)
    
    @field_validator("message_1", "message_2")
    @classmethod
    def validate_urls_in_message(cls, v: Optional[str]) -> Optional[str]:
        """Valide les URLs présentes dans le message"""
        if v is None:
            return v
        # Pattern pour détecter les URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, v)
        for url in urls:
            # Validation basique du format URL
            if not re.match(r'^https?://[a-zA-Z0-9]', url):
                raise ValueError(f"URL invalide: {url}")
        return v


class CampaignUpdate(BaseModel):
    """Schéma pour la mise à jour d'une campagne"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    message_1: Optional[str] = Field(None, min_length=1)
    message_2: Optional[str] = None
    template_name: Optional[str] = Field(None, max_length=100)


class CampaignResponse(CampaignBase):
    """
    Schéma de réponse pour une campagne.
    
    Note: Les compteurs utilisent delivered_count et read_count pour la cohérence
    avec les webhooks Gupshup qui retournent ces statuts.
    
    Exigences: 7.5, 8.5
    """
    id: int
    status: str
    total_recipients: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_rate: float = 0.0
    
    class Config:
        from_attributes = True


class CampaignWithCategories(CampaignResponse):
    """Schéma de campagne avec ses catégories"""
    categories: List["CategoryBrief"] = []


class CategoryBrief(BaseModel):
    """Schéma bref pour une catégorie"""
    id: int
    name: str
    color: Optional[str] = None
    
    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    """
    Schéma pour les statistiques d'une campagne.
    
    Note: Les formules de calcul des statistiques restent identiques après la migration Gupshup.
    - success_rate = (delivered_count + read_count) / total * 100
    
    Exigences: 7.5
    """
    campaign_id: int
    total_recipients: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    pending_count: int
    success_rate: float


class CampaignRetryResult(BaseModel):
    """Schéma pour le résultat d'un retry de campagne"""
    campaign_id: int
    retried_count: int
    message: str


# Mise à jour des références forward
CampaignWithCategories.model_rebuild()

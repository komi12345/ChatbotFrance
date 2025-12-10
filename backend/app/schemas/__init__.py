# Schémas Pydantic
from app.schemas.auth import LoginRequest, Token, TokenData, RefreshTokenRequest
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserInDB
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithContacts
from app.schemas.contact import (
    ContactCreate, ContactUpdate, ContactResponse, ContactWithCategories,
    ContactImport, ContactImportResult
)
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignWithCategories,
    CampaignStats, CampaignRetryResult
)
from app.schemas.message import (
    MessageResponse, MessageWithContact, MessageStats, MessageDailyStats,
    MessageFilter, InteractionResponse, InteractionWithDetails
)

__all__ = [
    # Auth
    "LoginRequest", "Token", "TokenData", "RefreshTokenRequest",
    # User
    "UserCreate", "UserUpdate", "UserResponse", "UserInDB",
    # Category
    "CategoryCreate", "CategoryUpdate", "CategoryResponse", "CategoryWithContacts",
    # Contact
    "ContactCreate", "ContactUpdate", "ContactResponse", "ContactWithCategories",
    "ContactImport", "ContactImportResult",
    # Campaign
    "CampaignCreate", "CampaignUpdate", "CampaignResponse", "CampaignWithCategories",
    "CampaignStats", "CampaignRetryResult",
    # Message
    "MessageResponse", "MessageWithContact", "MessageStats", "MessageDailyStats",
    "MessageFilter", "InteractionResponse", "InteractionWithDetails",
]

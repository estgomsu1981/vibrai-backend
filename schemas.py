from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
import humps
from sql_models import (
    AchievementCategory, MarketplaceListingType, 
    UserResponsiveness
)

# Esta función convierte snake_case (Python) a camelCase (JSON/JS)
def to_camel(string: str) -> str:
    return humps.camelize(string)

# Modelo base para que todos los esquemas usen la conversión a camelCase
class OrmModel(BaseModel):
    class Config:
        from_attributes = True
        alias_generator = to_camel
        populate_by_name = True

# --- Schemas de Entidades ---
class Achievement(OrmModel):
    id: str
    category: AchievementCategory
    description: str
    photo: Optional[str] = None
    date_added: datetime
    is_boosted: bool = False
    boost_expiry_date: Optional[datetime] = None

class MarketplaceListing(OrmModel):
    id: str
    user_id: str
    type: MarketplaceListingType
    title: str
    description: str
    photo: Optional[str] = None
    price: Optional[float] = None
    is_paid_ad: bool
    date_added: datetime
    expiry_date: Optional[datetime] = None
    was_successful_via_vibrai: Optional[bool] = None

class User(OrmModel):
    id: str
    name: str
    age: int
    bio: Optional[str] = None
    photos: List[str] = []
    primary_photo_url: Optional[str] = None
    interests: List[str] = []
    occupation: Optional[str] = None
    looking_for: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gender_identities: List[str] = []
    seeking_gender_identities: List[str] = []
    responsiveness_level: Optional[UserResponsiveness] = None
    is_premium: bool
    achievements: List[Achievement] = []
    marketplace_listings: List[MarketplaceListing] = []
    last_interaction_date: Optional[datetime] = None

# --- Schemas para Endpoints de API ---
class LikeResponse(OrmModel):
    is_match: bool
    match_profile: Optional[User] = None

# --- Schemas para el Router de IA ---
class ProfileAssistantRequest(BaseModel):
    user_message: str
    chat_history: List[Any]

class GenerateInterestsRequest(BaseModel):
    bio_text: str = Field(..., alias='bioText')

class SuggestIcebreakerRequest(BaseModel):
    user_name: str = Field(..., alias='userName')
    user_interests: Optional[List[str]] = Field(None, alias='userInterests')
    attempt_number: int = Field(..., alias='attemptNumber')

class SuggestRepliesRequest(BaseModel):
    last_message_text: str = Field(..., alias='lastMessageText')
    own_name: str = Field(..., alias='ownName')
    chat_partner_name: str = Field(..., alias='chatPartnerName')
    
class RewriteMessageRequest(BaseModel):
    original_message: str = Field(..., alias='originalMessage')
    rewrite_goal: str = Field(..., alias='rewriteGoal')
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Usamos alias para que el JSON (frontend) pueda ser camelCase
# mientras que nuestro código Python usa snake_case (PEP8)
class VibraiBaseModel(BaseModel):
    class Config:
        populate_by_name = True
        alias_generator = lambda string: ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(string.split('_')))

AchievementCategory = Literal['académico', 'vida', 'deportivo']
MarketplaceListingType = Literal['buscoTrabajo', 'vendoAlgo', 'ofrezcoTrabajo', 'otro']

class Achievement(VibraiBaseModel):
    id: str
    category: AchievementCategory
    description: str
    photo: Optional[str] = None
    date_added: str = Field(alias='dateAdded')
    is_boosted: Optional[bool] = Field(False, alias='isBoosted')
    boost_expiry_date: Optional[str] = Field(None, alias='boostExpiryDate')

class MarketplaceListing(VibraiBaseModel):
    id: str
    user_id: str = Field(alias='userId')
    type: MarketplaceListingType
    title: str
    description: str
    photo: Optional[str] = None
    price: Optional[float] = None
    is_paid_ad: bool = Field(alias='isPaidAd')
    date_added: str = Field(alias='dateAdded')
    expiry_date: Optional[str] = Field(None, alias='expiryDate')

class UserProfile(VibraiBaseModel):
    id: str
    name: str
    age: int
    bio: str
    photos: List[str]
    primary_photo_url: Optional[str] = Field(None, alias='primaryPhotoUrl')
    interests: List[str]
    occupation: Optional[str] = None
    looking_for: Optional[str] = Field(None, alias='lookingFor')
    country: Optional[str] = None
    achievements: List[Achievement]
    marketplace_listings: List[MarketplaceListing] = Field(alias='marketplaceListings')
    
    class Config:
        orm_mode = True # Para leer desde modelos SQLAlchemy

# Modelos para peticiones y respuestas de la API de IA
class IcebreakerRequest(VibraiBaseModel):
    user_name: str = Field(alias='userName')
    user_interests: Optional[List[str]] = Field([], alias='userInterests')
    attempt_number: int = Field(1, alias='attemptNumber')

class IcebreakerResponse(VibraiBaseModel):
    icebreaker: str

class ChatReplyRequest(VibraiBaseModel):
    last_message_text: str = Field(alias='lastMessageText')
    own_name: str = Field(alias='ownName')
    chat_partner_name: str = Field(alias='chatPartnerName')
    
class ChatReplyResponse(VibraiBaseModel):
    replies: List[str]
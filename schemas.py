from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime
import decimal

class Achievement(BaseModel):
    id: str
    user_id: str
    category: str
    description: str
    photo: Optional[str] = None
    date_added: datetime.datetime
    is_boosted: Optional[bool] = False
    boost_expiry_date: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)

class MarketplaceListing(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    description: str
    photo: Optional[str] = None
    price: Optional[decimal.Decimal] = None
    is_paid_ad: Optional[bool] = False
    date_added: datetime.datetime
    expiry_date: Optional[datetime.datetime] = None
    was_successful_via_vibrai: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    id: str
    name: str
    age: int
    bio: Optional[str] = None
    photos: Optional[List[str]] = []
    primary_photo_url: Optional[str] = None
    interests: Optional[List[str]] = []
    occupation: Optional[str] = None
    looking_for: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[decimal.Decimal] = None
    longitude: Optional[decimal.Decimal] = None
    gender_identities: Optional[List[str]] = []
    seeking_gender_identities: Optional[List[str]] = []
    is_premium: Optional[bool] = False
    achievements: List[Achievement] = []
    marketplace_listings: List[MarketplaceListing] = []
    model_config = ConfigDict(from_attributes=True)

class LikeResponse(BaseModel):
    is_match: bool
    match_profile: Optional[User] = None
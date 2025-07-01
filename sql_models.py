from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    Float,
    ForeignKey,
    ARRAY,
    DECIMAL
)
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    bio = Column(Text)
    photos = Column(ARRAY(String))
    primary_photo_url = Column(String)
    interests = Column(ARRAY(String))
    occupation = Column(String)
    looking_for = Column(String)
    country = Column(String)
    latitude = Column(DECIMAL(9, 6))
    longitude = Column(DECIMAL(9, 6))
    gender_identities = Column(ARRAY(String))
    seeking_gender_identities = Column(ARRAY(String))
    responsiveness_level = Column(String, default='medium')
    gift_balance = Column(Integer, default=0)
    interaction_score = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    last_interaction_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    achievements = relationship("Achievement", back_populates="owner")
    marketplace_listings = relationship("MarketplaceListing", back_populates="owner")

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    photo = Column(String)
    date_added = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    is_boosted = Column(Boolean, default=False)
    boost_expiry_date = Column(DateTime(timezone=True))
    
    owner = relationship("User", back_populates="achievements")

class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    photo = Column(String)
    price = Column(DECIMAL(10, 2))
    is_paid_ad = Column(Boolean, default=False)
    date_added = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    expiry_date = Column(DateTime(timezone=True))
    was_successful_via_vibrai = Column(Boolean)

    owner = relationship("User", back_populates="marketplace_listings")
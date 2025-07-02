import enum
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DECIMAL,
    TIMESTAMP, Enum, ForeignKey, PrimaryKeyConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Definición de los tipos ENUM de PostgreSQL
class AchievementCategoryEnum(enum.Enum):
    académico = 'académico'
    vida = 'vida'
    deportivo = 'deportivo'

class MarketplaceListingTypeEnum(enum.Enum):
    buscoTrabajo = 'buscoTrabajo'
    vendoAlgo = 'vendoAlgo'
    ofrezcoTrabajo = 'ofrezcoTrabajo'
    otro = 'otro'

class UserResponsivenessEnum(enum.Enum):
    high = 'high'
    medium = 'medium'
    low = 'low'

class ConnectionStatusEnum(enum.Enum):
    liked = 'liked'
    matched = 'matched'
    passed = 'passed'
    blocked = 'blocked'

# Modelos de SQLAlchemy
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
    country = Column(String, index=True)
    latitude = Column(DECIMAL(9, 6))
    longitude = Column(DECIMAL(9, 6))
    gender_identities = Column(ARRAY(String))
    seeking_gender_identities = Column(ARRAY(String))
    responsiveness_level = Column(Enum(UserResponsivenessEnum), default='medium')
    gift_balance = Column(Integer, default=0)
    interaction_score = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False, index=True)
    last_interaction_date = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    marketplace_listings = relationship("MarketplaceListing", back_populates="user", cascade="all, delete-orphan")

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(Enum(AchievementCategoryEnum), nullable=False)
    description = Column(Text, nullable=False)
    photo = Column(String)
    date_added = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_boosted = Column(Boolean, default=False)
    boost_expiry_date = Column(TIMESTAMP(timezone=True))
    
    user = relationship("User", back_populates="achievements")

class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(MarketplaceListingTypeEnum), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    photo = Column(String)
    price = Column(DECIMAL(10, 2))
    is_paid_ad = Column(Boolean, default=False)
    date_added = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expiry_date = Column(TIMESTAMP(timezone=True))
    was_successful_via_vibrai = Column(Boolean)
    
    user = relationship("User", back_populates="marketplace_listings")

class Connection(Base):
    __tablename__ = 'connections'
    user_liking_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user_liked_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ConnectionStatusEnum), nullable=False, default='liked')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint('user_liking_id', 'user_liked_id'),)
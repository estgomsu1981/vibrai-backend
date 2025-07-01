from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    DECIMAL,
    Enum,
    PrimaryKeyConstraint,
    ARRAY
)
from sqlalchemy.orm import relationship
from database import Base
import datetime

# Definición de los ENUM types para que SQLAlchemy los conozca
achievement_category_enum = Enum('académico', 'vida', 'deportivo', name='achievement_category')
marketplace_listing_type_enum = Enum('buscoTrabajo', 'vendoAlgo', 'ofrezcoTrabajo', 'otro', name='marketplace_listing_type')
user_responsiveness_enum = Enum('high', 'medium', 'low', name='user_responsiveness')
connection_status_enum = Enum('liked', 'matched', 'passed', 'blocked', name='connection_status')


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
    responsiveness_level = Column(user_responsiveness_enum, default='medium')
    gift_balance = Column(Integer, default=0)
    interaction_score = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    last_interaction_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    achievements = relationship("Achievement", back_populates="owner")
    marketplace_listings = relationship("MarketplaceListing", back_populates="owner")

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    category = Column(achievement_category_enum, nullable=False)
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
    type = Column(marketplace_listing_type_enum, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    photo = Column(String)
    price = Column(DECIMAL(10, 2))
    is_paid_ad = Column(Boolean, default=False)
    date_added = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    expiry_date = Column(DateTime(timezone=True))
    was_successful_via_vibrai = Column(Boolean)

    owner = relationship("User", back_populates="marketplace_listings")

class Connection(Base):
    __tablename__ = 'connections'
    user_liking_id = Column(String, ForeignKey('users.id'), nullable=False)
    user_liked_id = Column(String, ForeignKey('users.id'), nullable=False)
    status = Column(connection_status_enum, nullable=False, default='liked')
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    __table_args__ = (PrimaryKeyConstraint('user_liking_id', 'user_liked_id'),)
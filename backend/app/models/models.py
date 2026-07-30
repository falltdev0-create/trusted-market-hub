"""
app/models/models.py — نماذج قاعدة البيانات
User · Listing · ListingImage · ListingVerification
Conversation · Message · Notification
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime,
    Float, Integer, Enum, ForeignKey, JSON, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# ══════════════════════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════════════════════

class UserRole(str, enum.Enum):
    buyer       = "buyer"
    seller      = "seller"
    both        = "both"
    admin       = "admin"
    super_admin = "super_admin"  # legacy/display only; real hierarchy is in admins.role


class KYCStatus(str, enum.Enum):
    unverified = "unverified"
    pending    = "pending"
    verified   = "verified"
    rejected   = "rejected"
    # Legacy alias — some old code paths still reference `approved`
    approved   = "verified"


class ListingCategory(str, enum.Enum):
    house = "house"
    car   = "car"


class ListingType(str, enum.Enum):
    sale = "sale"
    rent = "rent"


class ConditionGrade(str, enum.Enum):
    excellent = "excellent"
    good      = "good"
    poor      = "poor"


class ListingStatus(str, enum.Enum):
    draft              = "draft"
    images_uploaded    = "images_uploaded"
    condition_assessed = "condition_assessed"
    docs_uploaded      = "docs_uploaded"
    docs_verified      = "docs_verified"
    price_set          = "price_set"
    pending_review     = "pending_review"
    published          = "published"
    rejected           = "rejected"
    sold               = "sold"


class DocMatchStatus(str, enum.Enum):
    pending  = "pending"
    approved = "approved"
    rejected = "rejected"


# ══════════════════════════════════════════════════════════════════════════════
# User
# ══════════════════════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id                   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email                = Column(String(255), unique=True, nullable=False, index=True)
    phone                = Column(String(20),  unique=True, nullable=False)
    password_hash        = Column(String(255), nullable=False)
    full_name            = Column(String(255), nullable=False)
    national_id          = Column(String(50),  unique=True, nullable=True)
    role                 = Column(Enum(UserRole), default=UserRole.both)
    is_verified          = Column(Boolean, default=False)
    is_active            = Column(Boolean, default=True)
    avatar_url           = Column(String(500), nullable=True)
    kyc_status           = Column(Enum(KYCStatus), default=KYCStatus.unverified)
    selfie_url           = Column(String(500), nullable=True)
    kyc_doc_url          = Column(String(500), nullable=True)
    disclaimer_signed    = Column(Boolean, default=False)
    disclaimer_signed_at = Column(DateTime, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listings      = relationship("Listing", back_populates="seller", lazy="selectin")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id",
                                 back_populates="sender")
    notifications = relationship("Notification", back_populates="user")


# ══════════════════════════════════════════════════════════════════════════════
# Listing
# ══════════════════════════════════════════════════════════════════════════════

class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listing_cat_type_status", "category", "listing_type", "status"),
        Index("ix_listing_city_status",     "city", "status"),
    )

    id               = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id        = Column(String(36), ForeignKey("users.id"), nullable=False)
    category         = Column(Enum(ListingCategory), nullable=False)
    listing_type     = Column(Enum(ListingType), nullable=False)
    title            = Column(String(255), nullable=False)
    description      = Column(Text, nullable=True)
    status           = Column(Enum(ListingStatus), default=ListingStatus.draft, index=True)
    city             = Column(String(100), nullable=True)
    district         = Column(String(100), nullable=True)
    price            = Column(Float, nullable=True)
    price_max_limit  = Column(Float, nullable=True)
    price_tier       = Column(Enum("cheap", "medium", "expensive", name="price_tier_enum"), nullable=True)
    suggested_min    = Column(Float, nullable=True)
    suggested_max    = Column(Float, nullable=True)
    currency         = Column(String(10), default="SDG")
    condition_grade  = Column(Enum(ConditionGrade), nullable=True)
    condition_score  = Column(Float, nullable=True)
    condition_report = Column(JSON, nullable=True)
    details          = Column(JSON, nullable=True)   # {bedrooms, size, year, km, ...}
    view_count       = Column(Integer, default=0)
    published_at     = Column(DateTime, nullable=True)
    rejected_reason  = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller       = relationship("User", back_populates="listings")
    images       = relationship("ListingImage", back_populates="listing",
                                order_by="ListingImage.order", lazy="selectin")
    verification = relationship("ListingVerification", back_populates="listing",
                                uselist=False, lazy="selectin")


class ListingImage(Base):
    __tablename__ = "listing_images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


    listing_id = Column(String(36), ForeignKey("listings.id"), nullable=False)
    url        = Column(String(500), nullable=False)
    image_type = Column(String(50), default="item")   # item | exterior | interior
    order      = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="images")


class ListingVerification(Base):
    __tablename__ = "listing_verifications"

    id                = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id        = Column(String(36), ForeignKey("listings.id"),
                               unique=True, nullable=False)
    owner_id_doc_url  = Column(String(500), nullable=True)
    ownership_doc_url = Column(String(500), nullable=True)
    match_score       = Column(Float, nullable=True)
    match_status      = Column(Enum(DocMatchStatus), default=DocMatchStatus.pending)
    match_details     = Column(JSON, nullable=True)
    rejection_reason  = Column(Text, nullable=True)
    reviewed_by       = Column(String(36), nullable=True)
    reviewed_at       = Column(DateTime, nullable=True)
    verified_at       = Column(DateTime, nullable=True)

    listing = relationship("Listing", back_populates="verification")


# ══════════════════════════════════════════════════════════════════════════════
# Chat
# ══════════════════════════════════════════════════════════════════════════════

class Conversation(Base):
    __tablename__ = "conversations"

    id                   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id           = Column(String(36), ForeignKey("listings.id"), nullable=False)
    buyer_id             = Column(String(36), ForeignKey("users.id"),    nullable=False)
    seller_id            = Column(String(36), ForeignKey("users.id"),    nullable=False)
    disclaimer_signed    = Column(Boolean, default=False)
    disclaimer_signed_at = Column(DateTime, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation",
                            order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    sender_id       = Column(String(36), ForeignKey("users.id"), nullable=False)
    content         = Column(Text, nullable=False)
    was_filtered    = Column(Boolean, default=False)
    is_read         = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    sender       = relationship("User", foreign_keys=[sender_id],
                                back_populates="sent_messages")


# ══════════════════════════════════════════════════════════════════════════════
# Notification
# ══════════════════════════════════════════════════════════════════════════════

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


    user_id    = Column(String(36), ForeignKey("users.id"), nullable=False)
    type       = Column(String(50), nullable=False)
    title      = Column(String(255), nullable=False)
    body       = Column(Text, nullable=True)
    is_read    = Column(Boolean, default=False)
    payload    = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

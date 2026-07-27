"""
Database Models — نماذج قاعدة البيانات
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Float,
    Integer, Enum, ForeignKey, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    buyer  = "buyer"
    seller = "seller"
    both   = "both"
    admin  = "admin"


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


class VerificationStatus(str, enum.Enum):
    pending  = "pending"
    approved = "approved"
    rejected = "rejected"


# ── User Model ───────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email          = Column(String(255), unique=True, nullable=False, index=True)
    phone          = Column(String(20), unique=True, nullable=False)
    password_hash  = Column(String(255), nullable=False)
    full_name      = Column(String(255), nullable=False)
    national_id    = Column(String(50), unique=True, nullable=True)  # set after KYC
    role           = Column(Enum(UserRole), default=UserRole.both)
    is_verified    = Column(Boolean, default=False)
    is_active      = Column(Boolean, default=True)
    avatar_url     = Column(String(500), nullable=True)
    kyc_status     = Column(Enum(VerificationStatus), default=VerificationStatus.pending)
    kyc_doc_url    = Column(String(500), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listings       = relationship("Listing", back_populates="seller")
    sent_messages  = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")


# ── Listing Model ─────────────────────────────────────────────────────────────

class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listings_category_type_status", "category", "listing_type", "status"),
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category        = Column(Enum(ListingCategory), nullable=False)
    listing_type    = Column(Enum(ListingType), nullable=False)
    title           = Column(String(255), nullable=False)
    description     = Column(Text, nullable=True)
    status          = Column(Enum(ListingStatus), default=ListingStatus.draft)

    # Price
    price           = Column(Float, nullable=True)
    price_max_limit = Column(Float, nullable=True)
    currency        = Column(String(10), default="SDG")

    # Location
    city            = Column(String(100), nullable=True)
    district        = Column(String(100), nullable=True)
    latitude        = Column(Float, nullable=True)
    longitude       = Column(Float, nullable=True)

    # Condition AI result
    condition_grade = Column(Enum(ConditionGrade), nullable=True)
    condition_score = Column(Float, nullable=True)
    condition_report= Column(JSON, nullable=True)

    # Extra details (flexible JSON)
    details         = Column(JSON, nullable=True)

    # Media
    images          = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    verification    = relationship("ListingVerification", back_populates="listing", uselist=False)

    seller          = relationship("User", back_populates="listings")
    conversations   = relationship("Conversation", back_populates="listing")

    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at    = Column(DateTime, nullable=True)


class ListingImage(Base):
    __tablename__ = "listing_images"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id  = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    url         = Column(String(500), nullable=False)
    image_type  = Column(String(50), nullable=True)  # "interior", "exterior", "doc"
    order       = Column(Integer, default=0)
    listing     = relationship("Listing", back_populates="images")


# ── Verification Model ────────────────────────────────────────────────────────

class ListingVerification(Base):
    __tablename__ = "listing_verifications"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id            = Column(UUID(as_uuid=True), ForeignKey("listings.id"), unique=True)
    owner_id_doc_url      = Column(String(500), nullable=True)   # national ID scan
    ownership_doc_url     = Column(String(500), nullable=True)   # title deed / car registration
    match_score           = Column(Float, nullable=True)          # 0-100
    match_status          = Column(Enum(VerificationStatus), default=VerificationStatus.pending)
    match_details         = Column(JSON, nullable=True)
    reviewed_by           = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at           = Column(DateTime, nullable=True)
    rejection_reason      = Column(Text, nullable=True)
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing               = relationship("Listing", back_populates="verification")


# ── Chat Models ───────────────────────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id      = Column(UUID(as_uuid=True), ForeignKey("listings.id"))
    buyer_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    seller_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    disclaimer_signed = Column(Boolean, default=False)
    disclaimer_signed_at = Column(DateTime, nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    listing         = relationship("Listing", back_populates="conversations")
    messages        = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    sender_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content         = Column(Text, nullable=False)
    is_read         = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    conversation    = relationship("Conversation", back_populates="messages")
    sender          = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")

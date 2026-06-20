"""
models.py  –  SQLAlchemy ORM models for ArtBazaar.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from database import Base
import enum


# ── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    artist = "artist"
    buyer  = "buyer"
    admin  = "admin"


class OrderStatus(str, enum.Enum):
    pending    = "pending"
    confirmed  = "confirmed"
    shipped    = "shipped"
    delivered  = "delivered"
    cancelled  = "cancelled"


class CustomOrderStatus(str, enum.Enum):
    pending   = "pending"
    accepted  = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    rejected  = "rejected"


class ArtworkCategory(str, enum.Enum):
    painting    = "painting"
    sculpture   = "sculpture"
    photography = "photography"
    digital     = "digital"
    textile     = "textile"
    ceramics    = "ceramics"
    jewellery   = "jewellery"
    other       = "other"


# ── User ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    full_name     = Column(String(120), nullable=False)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.buyer, nullable=False)
    avatar_url    = Column(String(500), nullable=True)
    bio           = Column(Text, nullable=True)
    location      = Column(String(120), nullable=True)
    is_active     = Column(Boolean, default=True)
    is_verified   = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    artworks      = relationship("Artwork", back_populates="artist", cascade="all, delete-orphan")
    orders        = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    reviews       = relationship("Review", back_populates="reviewer", cascade="all, delete-orphan")
    custom_orders_sent     = relationship("CustomOrder", back_populates="buyer", foreign_keys="CustomOrder.buyer_id")
    custom_orders_received = relationship("CustomOrder", back_populates="artist", foreign_keys="CustomOrder.artist_id")
    wishlist      = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


# ── Artwork ────────────────────────────────────────────────────────────────

class Artwork(Base):
    __tablename__ = "artworks"

    id            = Column(Integer, primary_key=True, index=True)
    artist_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    title         = Column(String(200), nullable=False)
    description   = Column(Text, nullable=True)
    price         = Column(Float, nullable=False)
    category      = Column(SAEnum(ArtworkCategory), nullable=False)
    tags          = Column(JSON, default=list)       # list of strings
    medium        = Column(String(100), nullable=True)   # oil, acrylic, watercolour…
    dimensions    = Column(String(100), nullable=True)   # e.g. "30x40 cm"
    is_available  = Column(Boolean, default=True)
    is_featured   = Column(Boolean, default=False)
    stock         = Column(Integer, default=1)
    image_urls    = Column(JSON, default=list)       # list of image URLs
    embedding     = Column(JSON, nullable=True)      # for similarity search
    view_count    = Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    artist        = relationship("User", back_populates="artworks")
    order_items   = relationship("OrderItem", back_populates="artwork")
    reviews       = relationship("Review", back_populates="artwork", cascade="all, delete-orphan")
    wishlisted_by = relationship("Wishlist", back_populates="artwork", cascade="all, delete-orphan")


# ── Order ──────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id            = Column(Integer, primary_key=True, index=True)
    buyer_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    status        = Column(SAEnum(OrderStatus), default=OrderStatus.pending)
    total_amount  = Column(Float, nullable=False)
    shipping_address = Column(Text, nullable=True)
    notes         = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer         = relationship("User", back_populates="orders", foreign_keys=[buyer_id])
    items         = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    quantity   = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)

    order      = relationship("Order", back_populates="items")
    artwork    = relationship("Artwork", back_populates="order_items")


# ── Review ─────────────────────────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id          = Column(Integer, primary_key=True, index=True)
    artwork_id  = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating      = Column(Integer, nullable=False)        # 1–5
    comment     = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    artwork     = relationship("Artwork", back_populates="reviews")
    reviewer    = relationship("User", back_populates="reviews")


# ── Custom Order ──────────────────────────────────────────────────────────

class CustomOrder(Base):
    __tablename__ = "custom_orders"

    id            = Column(Integer, primary_key=True, index=True)
    buyer_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    artist_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    title         = Column(String(200), nullable=False)
    description   = Column(Text, nullable=False)
    budget        = Column(Float, nullable=True)
    deadline      = Column(DateTime, nullable=True)
    reference_images = Column(JSON, default=list)
    status        = Column(SAEnum(CustomOrderStatus), default=CustomOrderStatus.pending)
    artist_notes  = Column(Text, nullable=True)
    agreed_price  = Column(Float, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer         = relationship("User", back_populates="custom_orders_sent",     foreign_keys=[buyer_id])
    artist        = relationship("User", back_populates="custom_orders_received", foreign_keys=[artist_id])


# ── Wishlist ───────────────────────────────────────────────────────────────

class Wishlist(Base):
    __tablename__ = "wishlist"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="wishlist")
    artwork    = relationship("Artwork", back_populates="wishlisted_by")


# ── Notification ──────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String(200), nullable=False)
    message    = Column(Text, nullable=False)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="notifications")

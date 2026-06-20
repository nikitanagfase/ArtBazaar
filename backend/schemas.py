"""
schemas.py  –  Pydantic v2 request/response models for ArtBazaar.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from models import ArtworkCategory, OrderStatus, CustomOrderStatus, UserRole


# ══════════════════════════════════════════════════════════════════
#  Auth / User
# ══════════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    full_name: str  = Field(..., min_length=2, max_length=120)
    email:     EmailStr
    password:  str  = Field(..., min_length=6)
    role:      UserRole = UserRole.buyer

class UserLogin(BaseModel):
    email:    EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str]     = None
    bio:       Optional[str]     = None
    location:  Optional[str]     = None
    avatar_url: Optional[str]    = None

class UserOut(BaseModel):
    id:         int
    full_name:  str
    email:      str
    role:       UserRole
    avatar_url: Optional[str] = None
    bio:        Optional[str] = None
    location:   Optional[str] = None
    is_active:  bool
    created_at: datetime

    model_config = {"from_attributes": True}

class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserOut


# ══════════════════════════════════════════════════════════════════
#  Artwork
# ══════════════════════════════════════════════════════════════════

class ArtworkCreate(BaseModel):
    title:       str            = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    price:       float          = Field(..., gt=0)
    category:    ArtworkCategory
    tags:        List[str]      = []
    medium:      Optional[str]  = None
    dimensions:  Optional[str]  = None
    stock:       int            = Field(1, ge=1)

class ArtworkUpdate(BaseModel):
    title:        Optional[str]             = None
    description:  Optional[str]             = None
    price:        Optional[float]           = None
    category:     Optional[ArtworkCategory] = None
    tags:         Optional[List[str]]       = None
    medium:       Optional[str]             = None
    dimensions:   Optional[str]             = None
    stock:        Optional[int]             = None
    is_available: Optional[bool]            = None

class ArtworkOut(BaseModel):
    id:           int
    artist_id:    int
    title:        str
    description:  Optional[str]
    price:        float
    category:     ArtworkCategory
    tags:         List[str]
    medium:       Optional[str]
    dimensions:   Optional[str]
    is_available: bool
    is_featured:  bool
    stock:        int
    image_urls:   List[str]
    view_count:   int
    created_at:   datetime
    artist:       UserOut

    model_config = {"from_attributes": True}

class ArtworkListOut(BaseModel):
    id:           int
    artist_id:    int
    title:        str
    price:        float
    category:     ArtworkCategory
    tags:         List[str]
    is_available: bool
    image_urls:   List[str]
    view_count:   int
    created_at:   datetime
    artist:       UserOut

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════
#  Order
# ══════════════════════════════════════════════════════════════════

class OrderItemCreate(BaseModel):
    artwork_id: int
    quantity:   int = Field(1, ge=1)

class OrderCreate(BaseModel):
    items:            List[OrderItemCreate]
    shipping_address: Optional[str] = None
    notes:            Optional[str] = None

class OrderItemOut(BaseModel):
    id:         int
    artwork_id: int
    quantity:   int
    unit_price: float
    artwork:    ArtworkListOut

    model_config = {"from_attributes": True}

class OrderOut(BaseModel):
    id:               int
    buyer_id:         int
    status:           OrderStatus
    total_amount:     float
    shipping_address: Optional[str]
    notes:            Optional[str]
    created_at:       datetime
    items:            List[OrderItemOut]

    model_config = {"from_attributes": True}

class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ══════════════════════════════════════════════════════════════════
#  Review
# ══════════════════════════════════════════════════════════════════

class ReviewCreate(BaseModel):
    rating:  int     = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewOut(BaseModel):
    id:          int
    artwork_id:  int
    reviewer_id: int
    rating:      int
    comment:     Optional[str]
    created_at:  datetime
    reviewer:    UserOut

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════
#  Custom Order
# ══════════════════════════════════════════════════════════════════

class CustomOrderCreate(BaseModel):
    artist_id:   int
    title:       str            = Field(..., min_length=2, max_length=200)
    description: str            = Field(..., min_length=10)
    budget:      Optional[float] = None
    deadline:    Optional[datetime] = None

class CustomOrderUpdate(BaseModel):
    status:       Optional[CustomOrderStatus] = None
    artist_notes: Optional[str]               = None
    agreed_price: Optional[float]             = None

class CustomOrderOut(BaseModel):
    id:               int
    buyer_id:         int
    artist_id:        int
    title:            str
    description:      str
    budget:           Optional[float]
    deadline:         Optional[datetime]
    reference_images: List[str]
    status:           CustomOrderStatus
    artist_notes:     Optional[str]
    agreed_price:     Optional[float]
    created_at:       datetime
    buyer:            UserOut
    artist:           UserOut

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════
#  Wishlist / Notification
# ══════════════════════════════════════════════════════════════════

class WishlistOut(BaseModel):
    id:         int
    artwork_id: int
    created_at: datetime
    artwork:    ArtworkListOut

    model_config = {"from_attributes": True}

class NotificationOut(BaseModel):
    id:         int
    title:      str
    message:    str
    is_read:    bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════
#  AI
# ══════════════════════════════════════════════════════════════════

class AIDescriptionOut(BaseModel):
    title:       str
    description: str
    tags:        List[str]

class SimilarArtworkOut(BaseModel):
    artwork: ArtworkListOut
    score:   float


# ══════════════════════════════════════════════════════════════════
#  Analytics (Artist Dashboard)
# ══════════════════════════════════════════════════════════════════

class ArtistAnalytics(BaseModel):
    total_artworks:      int
    total_orders:        int
    total_revenue:       float
    pending_orders:      int
    average_rating:      float
    top_category:        Optional[str]
    monthly_revenue:     List[dict]   # [{month, revenue}]
    recent_orders:       List[OrderOut]

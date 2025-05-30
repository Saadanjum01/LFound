from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime, date
from enum import Enum

# Enums for better type safety
class ItemType(str, Enum):
    LOST = "lost"
    FOUND = "found"

class ItemCategory(str, Enum):
    ELECTRONICS = "electronics"
    BAGS = "bags"
    JEWELRY = "jewelry"
    CLOTHING = "clothing"
    PERSONAL = "personal"
    BOOKS = "books"
    SPORTS = "sports"
    OTHER = "other"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ItemStatus(str, Enum):
    ACTIVE = "active"
    CLAIMED = "claimed"
    RESOLVED = "resolved"
    ARCHIVED = "archived"

class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

# User Models
class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime

class UserProfileCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

# Item Models
class ItemBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: ItemCategory
    location: str = Field(..., min_length=2, max_length=100)
    images: List[str] = Field(default_factory=list)
    reward: Optional[int] = Field(default=0, ge=0)
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM

class ItemCreate(ItemBase):
    type: ItemType
    date_lost: Optional[date] = None
    time_lost: Optional[str] = None
    contact_preference: Literal["email", "phone"] = "email"

class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[ItemCategory] = None
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    reward: Optional[int] = Field(None, ge=0)
    urgency: Optional[UrgencyLevel] = None
    status: Optional[ItemStatus] = None

class Item(ItemBase):
    id: str
    type: ItemType
    user_id: str
    date_lost: Optional[date] = None
    time_lost: Optional[str] = None
    status: ItemStatus = ItemStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None

# Claim Request Models
class ClaimRequestBase(BaseModel):
    message: str = Field(..., min_length=10, max_length=1000)

class ClaimRequestCreate(ClaimRequestBase):
    item_id: str

class ClaimRequest(ClaimRequestBase):
    id: str
    item_id: str
    claimer_id: str
    status: ClaimStatus = ClaimStatus.PENDING
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    claimer_name: Optional[str] = None
    claimer_email: Optional[str] = None
    item_title: Optional[str] = None

class ClaimRequestUpdate(BaseModel):
    status: ClaimStatus
    admin_notes: Optional[str] = None

# Response Models
class ItemListResponse(BaseModel):
    items: List[Item]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class DashboardStats(BaseModel):
    total_items_posted: int
    items_recovered: int
    helping_others: int
    success_rate: float

class DashboardData(BaseModel):
    stats: DashboardStats
    recent_items: List[Item]
    claim_requests: List[ClaimRequest]

# Search and Filter Models
class ItemSearchParams(BaseModel):
    search: Optional[str] = None
    category: Optional[ItemCategory] = None
    location: Optional[str] = None
    urgency: Optional[UrgencyLevel] = None
    has_reward: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=12, ge=1, le=50)

# Authentication Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)

# File Upload Models
class ImageUploadResponse(BaseModel):
    url: str
    public_url: str
    path: str 
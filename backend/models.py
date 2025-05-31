import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from beanie import Document
from enum import Enum

# Enums
class ItemType(str, Enum):
    LOST = "lost"
    FOUND = "found"

class ItemStatus(str, Enum):
    ACTIVE = "active"
    CLAIMED = "claimed"
    RESOLVED = "resolved"

class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AdminActionType(str, Enum):
    APPROVE_CLAIM = "approve_claim"
    REJECT_CLAIM = "reject_claim"
    REMOVE_ITEM = "remove_item"
    BAN_USER = "ban_user"

class DisputeStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"

# MongoDB Document Models
class Profile(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_admin: bool = False
    is_banned: bool = False
    
    class Settings:
        name = "profiles"
        indexes = [
            "email",
            "id",
        ]

class Item(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    category: str
    location: str
    date_lost_found: datetime
    item_type: ItemType
    status: ItemStatus = ItemStatus.ACTIVE
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    image_urls: List[str] = []
    reward_amount: Optional[float] = None
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "items"
        indexes = [
            "user_id",
            "item_type",
            "status",
            "category",
            "created_at",
            "id",
        ]

class ClaimRequest(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    claimant_id: str
    item_owner_id: str
    description: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    status: ClaimStatus = ClaimStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    admin_notes: Optional[str] = None
    
    class Settings:
        name = "claim_requests"
        indexes = [
            "item_id",
            "claimant_id",
            "item_owner_id",
            "status",
            "created_at",
            "id",
        ]

class AdminAction(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action_type: AdminActionType
    target_id: str  # ID of the item, claim, or user being acted upon
    reason: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "admin_actions"
        indexes = [
            "admin_id",
            "action_type",
            "target_id",
            "created_at",
            "id",
        ]

class Dispute(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_id: str
    reported_by: str
    reason: str
    description: str
    status: DisputeStatus = DisputeStatus.OPEN
    admin_assigned: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "disputes"
        indexes = [
            "claim_id",
            "reported_by",
            "status",
            "admin_assigned",
            "created_at",
            "id",
        ]

# Pydantic Response Models (for API responses)
class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime
    is_admin: bool
    is_banned: bool

class ItemResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    category: str
    location: str
    date_lost_found: datetime
    item_type: ItemType
    status: ItemStatus
    contact_email: str
    contact_phone: Optional[str]
    image_urls: List[str]
    reward_amount: Optional[float]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

class ClaimResponse(BaseModel):
    id: str
    item_id: str
    claimant_id: str
    item_owner_id: str
    description: str
    contact_email: str
    contact_phone: Optional[str]
    status: ClaimStatus
    created_at: datetime
    admin_notes: Optional[str]

class AdminActionResponse(BaseModel):
    id: str
    admin_id: str
    action_type: AdminActionType
    target_id: str
    reason: Optional[str]
    details: Optional[str]
    created_at: datetime

class DisputeResponse(BaseModel):
    id: str
    claim_id: str
    reported_by: str
    reason: str
    description: str
    status: DisputeStatus
    admin_assigned: Optional[str]
    resolution: Optional[str]
    created_at: datetime

# Request Models (for API requests)
class ProfileCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class ItemCreate(BaseModel):
    title: str
    description: str
    category: str
    location: str
    date_lost_found: datetime
    item_type: ItemType
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    reward_amount: Optional[float] = None
    tags: List[str] = []

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    date_lost_found: Optional[datetime] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    reward_amount: Optional[float] = None
    tags: Optional[List[str]] = None
    status: Optional[ItemStatus] = None

class ClaimCreate(BaseModel):
    item_id: str
    description: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminActionCreate(BaseModel):
    action_type: AdminActionType
    target_id: str
    reason: Optional[str] = None
    details: Optional[str] = None

class DisputeCreate(BaseModel):
    claim_id: str
    reason: str
    description: str

class FileUploadResponse(BaseModel):
    url: str
    public_url: str
    path: str
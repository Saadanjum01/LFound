import os
import uuid
import shutil
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt

# Import models and database
try:
    from models import (
        Profile, Item, ClaimRequest, AdminAction, Dispute,
        ProfileCreate, ProfileUpdate, ProfileResponse,
        ItemCreate, ItemUpdate, ItemResponse,
        ClaimCreate, ClaimResponse,
        AdminActionCreate, AdminActionResponse,
        DisputeCreate, DisputeResponse,
        LoginRequest, FileUploadResponse,
        ItemType, ItemStatus, ClaimStatus, AdminActionType, DisputeStatus
    )
    from database import init_database, close_mongo_connection, test_connection
    from config import settings
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from models import (
        Profile, Item, ClaimRequest, AdminAction, Dispute,
        ProfileCreate, ProfileUpdate, ProfileResponse,
        ItemCreate, ItemUpdate, ItemResponse,
        ClaimCreate, ClaimResponse,
        AdminActionCreate, AdminActionResponse,
        DisputeCreate, DisputeResponse,
        LoginRequest, FileUploadResponse,
        ItemType, ItemStatus, ClaimStatus, AdminActionType, DisputeStatus
    )
    from database import init_database, close_mongo_connection, test_connection
    from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Lost & Found Portal API",
    description="API for managing lost and found items",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create upload directory
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Profile:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await Profile.find_one(Profile.id == user_id)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: Profile = Depends(get_current_user)) -> Profile:
    if current_user.is_banned:
        raise HTTPException(status_code=400, detail="Banned user")
    return current_user

async def get_current_admin_user(current_user: Profile = Depends(get_current_active_user)) -> Profile:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await init_database()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# API Routes

# Health check
@app.get("/api/health")
async def health_check():
    db_status = await test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.utcnow()
    }

# Authentication endpoints
@app.post("/api/auth/register", response_model=dict)
async def register(user_data: ProfileCreate):
    # Check if user already exists
    existing_user = await Profile.find_one(Profile.email == user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = Profile(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hashed_password
    )
    
    await new_user.insert()
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": ProfileResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            created_at=new_user.created_at,
            is_admin=new_user.is_admin,
            is_banned=new_user.is_banned
        )
    }

@app.post("/api/auth/login", response_model=dict)
async def login(credentials: LoginRequest):
    user = await Profile.find_one(Profile.email == credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if user.is_banned:
        raise HTTPException(status_code=400, detail="Account has been banned")
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": ProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            is_admin=user.is_admin,
            is_banned=user.is_banned
        )
    }

@app.get("/api/auth/me", response_model=ProfileResponse)
async def get_current_user_info(current_user: Profile = Depends(get_current_active_user)):
    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        is_admin=current_user.is_admin,
        is_banned=current_user.is_banned
    )

# Profile endpoints
@app.put("/api/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: Profile = Depends(get_current_active_user)
):
    update_data = profile_data.dict(exclude_unset=True)
    if update_data:
        # Check email uniqueness if email is being updated
        if "email" in update_data:
            existing_user = await Profile.find_one(
                Profile.email == update_data["email"],
                Profile.id != current_user.id
            )
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already in use")
        
        update_data["updated_at"] = datetime.utcnow()
        await current_user.update({"$set": update_data})
        await current_user.save()
    
    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        is_admin=current_user.is_admin,
        is_banned=current_user.is_banned
    )

# Item endpoints
@app.get("/api/items", response_model=List[ItemResponse])
async def get_items(
    item_type: Optional[ItemType] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[ItemStatus] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    skip: int = Query(0, ge=0)
):
    # Build query filters
    filters = {}
    if item_type:
        filters["item_type"] = item_type
    if category:
        filters["category"] = category
    if status:
        filters["status"] = status
    else:
        filters["status"] = ItemStatus.ACTIVE  # Default to active items
    
    # Create query
    query = Item.find(filters)
    
    # Add text search if provided
    if search:
        query = query.find({"$text": {"$search": search}})
    
    # Apply pagination and sorting
    items = await query.sort([("created_at", -1)]).skip(skip).limit(limit).to_list()
    
    return [ItemResponse(**item.dict()) for item in items]

@app.get("/api/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    item = await Item.find_one(Item.id == item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return ItemResponse(**item.dict())

@app.post("/api/items", response_model=ItemResponse)
async def create_item(
    item_data: ItemCreate,
    current_user: Profile = Depends(get_current_active_user)
):
    new_item = Item(
        **item_data.dict(),
        user_id=current_user.id
    )
    
    await new_item.insert()
    
    return ItemResponse(**new_item.dict())

@app.put("/api/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    item_data: ItemUpdate,
    current_user: Profile = Depends(get_current_active_user)
):
    item = await Item.find_one(Item.id == item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership or admin privileges
    if item.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this item")
    
    update_data = item_data.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await item.update({"$set": update_data})
        await item.save()
    
    return ItemResponse(**item.dict())

# File upload endpoint
@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: Profile = Depends(get_current_active_user)
):
    # Validate file type
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.max_file_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # Return file info
    return FileUploadResponse(
        url=f"/uploads/{unique_filename}",
        public_url=f"https://demobackend.emergentagent.com/uploads/{unique_filename}",
        path=str(file_path)
    )

# Claims endpoints
@app.post("/api/claims", response_model=ClaimResponse)
async def create_claim(
    claim_data: ClaimCreate,
    current_user: Profile = Depends(get_current_active_user)
):
    # Get the item
    item = await Item.find_one(Item.id == claim_data.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.status != ItemStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Item is not available for claims")
    
    if item.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot claim your own item")
    
    # Check if user already has a pending claim for this item
    existing_claim = await ClaimRequest.find_one(
        ClaimRequest.item_id == claim_data.item_id,
        ClaimRequest.claimant_id == current_user.id,
        ClaimRequest.status == ClaimStatus.PENDING
    )
    if existing_claim:
        raise HTTPException(status_code=400, detail="You already have a pending claim for this item")
    
    new_claim = ClaimRequest(
        **claim_data.dict(),
        claimant_id=current_user.id,
        item_owner_id=item.user_id
    )
    
    await new_claim.insert()
    
    return ClaimResponse(**new_claim.dict())

@app.get("/api/claims", response_model=List[ClaimResponse])
async def get_claims(
    status: Optional[ClaimStatus] = Query(None),
    current_user: Profile = Depends(get_current_active_user),
    limit: int = Query(20, le=100),
    skip: int = Query(0, ge=0)
):
    filters = {}
    if status:
        filters["status"] = status
    
    # Users can see claims they made or claims for their items
    # Admins can see all claims
    if not current_user.is_admin:
        filters["$or"] = [
            {"claimant_id": current_user.id},
            {"item_owner_id": current_user.id}
        ]
    
    claims = await ClaimRequest.find(filters).sort([("created_at", -1)]).skip(skip).limit(limit).to_list()
    
    return [ClaimResponse(**claim.dict()) for claim in claims]

# Dashboard endpoint
@app.get("/api/dashboard")
async def get_dashboard(current_user: Profile = Depends(get_current_active_user)):
    # Get user's items
    user_items = await Item.find(Item.user_id == current_user.id).to_list()
    
    # Get user's claims
    user_claims = await ClaimRequest.find(ClaimRequest.claimant_id == current_user.id).to_list()
    
    # Get claims for user's items
    claims_for_items = await ClaimRequest.find(ClaimRequest.item_owner_id == current_user.id).to_list()
    
    # Calculate stats
    total_items_posted = len(user_items)
    items_recovered = len([item for item in user_items if item.status == ItemStatus.RESOLVED])
    helping_others = len([claim for claim in user_claims if claim.status == ClaimStatus.APPROVED])
    success_rate = (items_recovered / total_items_posted * 100) if total_items_posted > 0 else 0
    
    return {
        "stats": {
            "total_items_posted": total_items_posted,
            "items_recovered": items_recovered,
            "helping_others": helping_others,
            "success_rate": round(success_rate, 1)
        },
        "recent_items": [ItemResponse(**item.dict()) for item in user_items[:5]],
        "recent_claims": [ClaimResponse(**claim.dict()) for claim in (user_claims + claims_for_items)[:5]]
    }

# Admin endpoints
@app.get("/api/admin/claims", response_model=List[ClaimResponse])
async def get_all_claims_admin(
    current_user: Profile = Depends(get_current_admin_user),
    status: Optional[ClaimStatus] = Query(None),
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0)
):
    filters = {}
    if status:
        filters["status"] = status
    
    claims = await ClaimRequest.find(filters).sort([("created_at", -1)]).skip(skip).limit(limit).to_list()
    
    return [ClaimResponse(**claim.dict()) for claim in claims]

@app.put("/api/admin/claims/{claim_id}")
async def update_claim_status(
    claim_id: str,
    status: ClaimStatus,
    admin_notes: Optional[str] = None,
    current_user: Profile = Depends(get_current_admin_user)
):
    claim = await ClaimRequest.find_one(ClaimRequest.id == claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Update claim
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    if admin_notes:
        update_data["admin_notes"] = admin_notes
    
    await claim.update({"$set": update_data})
    await claim.save()
    
    # If claim is approved, update item status
    if status == ClaimStatus.APPROVED:
        item = await Item.find_one(Item.id == claim.item_id)
        if item:
            await item.update({"$set": {"status": ItemStatus.CLAIMED, "updated_at": datetime.utcnow()}})
            await item.save()
    
    # Log admin action
    admin_action = AdminAction(
        admin_id=current_user.id,
        action_type=AdminActionType.APPROVE_CLAIM if status == ClaimStatus.APPROVED else AdminActionType.REJECT_CLAIM,
        target_id=claim_id,
        reason=admin_notes
    )
    await admin_action.insert()
    
    return {"message": "Claim status updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

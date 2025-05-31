import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import Profile, Item, ClaimRequest, AdminAction, Dispute
from config import settings

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None

# MongoDB connection instance
mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    mongodb.client = AsyncIOMotorClient(settings.mongo_url)
    
    # Initialize beanie with the Product document class and a database
    await init_beanie(
        database=mongodb.client[settings.database_name],
        document_models=[
            Profile,
            Item, 
            ClaimRequest,
            AdminAction,
            Dispute
        ]
    )
    print("Connected to MongoDB")

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        print("Disconnected from MongoDB")

async def get_database():
    """Get database instance"""
    return mongodb.client[settings.database_name]

# Helper functions for testing connection
async def test_connection():
    """Test database connection"""
    try:
        # The ismaster command is cheap and does not require auth.
        await mongodb.client.admin.command('ismaster')
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def create_indexes():
    """Create additional indexes if needed"""
    try:
        db = await get_database()
        
        # Additional compound indexes for better query performance
        await db.items.create_index([("item_type", 1), ("status", 1), ("created_at", -1)])
        await db.items.create_index([("category", 1), ("item_type", 1)])
        await db.claim_requests.create_index([("item_id", 1), ("status", 1)])
        await db.profiles.create_index([("email", 1)], unique=True)
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")

# Initialize database on startup
async def init_database():
    """Initialize database connection and setup"""
    await connect_to_mongo()
    await create_indexes()
    
    # Create default admin user if doesn't exist
    await create_default_admin()

async def create_default_admin():
    """Create default admin user for testing"""
    try:
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Check if admin exists
        admin_exists = await Profile.find_one(Profile.email == "admin@lostfound.com")
        
        if not admin_exists:
            admin_user = Profile(
                email="admin@lostfound.com",
                full_name="System Administrator",
                password_hash=pwd_context.hash("admin123"),
                is_admin=True
            )
            await admin_user.insert()
            print("Default admin user created: admin@lostfound.com / admin123")
        else:
            print("Admin user already exists")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")

# Utility function to get collection directly if needed
async def get_collection(collection_name: str):
    """Get collection instance"""
    db = await get_database()
    return db[collection_name]
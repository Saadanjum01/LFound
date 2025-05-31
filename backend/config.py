import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB Configuration
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "lost_found_portal")
    
    # Application Settings
    environment: str = os.getenv("ENVIRONMENT", "development")
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-this")
    allowed_origins: List[str] = [
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://10.64.129.37:3000",
        "https://demobackend.emergentagent.com",
        "https://demofrontend.emergentagent.com",
        "*"  # Allow all origins for development
    ]
    
    # JWT Settings
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # File Upload Settings
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    allowed_file_types: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    class Config:
        env_file = ".env"

settings = Settings() 
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CampusPredict"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "campuspredict-super-secret-production-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database: Default to local SQLite fallback if PostgreSQL is not specified
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./campuspredict.db"
    )
    
    # Redis Cache (optional with in-memory fallback)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_EXPIRATION_SECONDS: int = 3600
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR.parent / "data"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MODEL_DIR: Path = BASE_DIR / "saved_models"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
(settings.DATA_DIR / "sample").mkdir(parents=True, exist_ok=True)
(settings.DATA_DIR / "templates").mkdir(parents=True, exist_ok=True)

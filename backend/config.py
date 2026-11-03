import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    PROJECT_NAME = "CampusPredict"
    VERSION = "2.0.0"
    SECRET_KEY = os.getenv("SECRET_KEY", "campuspredict-flask-jwt-secret-key-2026")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours
    
    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "campuspredict.db"))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
    
    # Model and artifact directories
    MODEL_DIR = BASE_DIR / "saved_models"
    UPLOAD_DIR = BASE_DIR / "uploads"
    REPORTS_DIR = BASE_DIR / "reports"
    
    # Server
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")

# Ensure required directories exist
Config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

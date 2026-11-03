from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional, Dict, Any
import bcrypt
import jwt
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database import SessionLocal
from models.schemas_db import User

def hash_password(password: str) -> str:
    """Hashes a password using Werkzeug's default modern hashing algorithm."""
    return generate_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against either bcrypt or werkzeug hashes.
    Ensures backward compatibility with existing users in campuspredict.db.
    """
    if not hashed_password or not plain_password:
        return False
    
    # Check if stored as bcrypt hash ($2a$, $2b$, $2y$)
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            plain_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(plain_bytes, hash_bytes)
        except Exception:
            return False
    
    # Otherwise check using Werkzeug
    try:
        return check_password_hash(hashed_password, plain_password)
    except Exception:
        return False

def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a secure JWT access token containing subject, user_id, and role."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role or "student",
        "exp": expire
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

def login_required(f):
    """
    Flask decorator that enforces authentication via Authorization: Bearer <token>.
    Sets g.current_user for the request context.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication token required", "detail": "Missing or malformed Authorization header"}), 401
        
        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token", "detail": "Please log in again"}), 401
        
        username = payload.get("sub")
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user or not user.is_active:
                return jsonify({"error": "User not found or account disabled"}), 401
            # Detach user representation for current context
            g.current_user = user
            g.user_id = user.id
            g.username = user.username
            g.role = user.role
            return f(*args, **kwargs)
        finally:
            db.close()
    return decorated

def admin_required(f):
    """Decorator ensuring current user possesses admin privileges."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if getattr(g, "role", "") != "admin":
            return jsonify({"error": "Forbidden", "detail": "Administrative privileges required"}), 403
        return f(*args, **kwargs)
    return decorated

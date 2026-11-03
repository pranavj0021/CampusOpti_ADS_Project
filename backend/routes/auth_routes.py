import re
from flask import Blueprint, request, jsonify, g
from database import SessionLocal
from models.schemas_db import User, StudentProfile
from services.auth_service import (
    hash_password, verify_password, create_access_token, login_required
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()
    full_name = str(data.get("full_name", "")).strip() or username
    role = str(data.get("role", "student")).strip().lower()

    if not username or len(username) < 3:
        return jsonify({"error": "Validation Error", "detail": "Username must be at least 3 characters long"}), 400
    
    if not email or "@" not in email:
        return jsonify({"error": "Validation Error", "detail": "A valid email address is required"}), 400

    if not password or len(password) < 6:
        return jsonify({"error": "Validation Error", "detail": "Password must be at least 6 characters long"}), 400

    if role not in ("student", "admin", "faculty"):
        role = "student"

    db = SessionLocal()
    try:
        # Check existing username or email
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            if existing.username == username:
                return jsonify({"error": "Conflict", "detail": f"Username '{username}' is already taken"}), 400
            return jsonify({"error": "Conflict", "detail": f"Email '{email}' is already registered"}), 400

        # Create user
        new_user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create initial student profile if role is student
        profile = StudentProfile(
            user_id=new_user.id,
            roll_number=f"STU{new_user.id:04d}",
            department_code="CS",
            cgpa=7.5,
            backlogs=0,
            internships_count=1,
            projects_count=2,
            certifications_count=1,
            coding_score=75.0,
            communication_score=80.0
        )
        db.add(profile)
        db.commit()

        token = create_access_token(new_user)
        return jsonify({
            "message": "User registered successfully",
            "access_token": token,
            "token_type": "bearer",
            "user": new_user.to_dict()
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Registration Error", "detail": str(e)}), 500
    finally:
        db.close()

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return jsonify({"error": "Validation Error", "detail": "Both username and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user or not verify_password(password, user.hashed_password):
            return jsonify({"error": "Unauthorized", "detail": "Invalid username or password"}), 401

        if not user.is_active:
            return jsonify({"error": "Forbidden", "detail": "This account has been deactivated"}), 403

        token = create_access_token(user)
        return jsonify({
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"error": "Login Error", "detail": str(e)}), 500
    finally:
        db.close()

@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    return jsonify({
        "user": g.current_user.to_dict()
    }), 200

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    # In stateless JWT architecture, the client discards the token
    return jsonify({
        "message": "Logged out successfully"
    }), 200

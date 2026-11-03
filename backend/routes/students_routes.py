import datetime
from flask import Blueprint, request, jsonify, g
from database import SessionLocal
from models.schemas_db import StudentProfile, User
from services.auth_service import login_required

students_bp = Blueprint("students", __name__, url_prefix="/api/students")

@students_bp.route("/profile", methods=["GET"])
@login_required
def get_student_profile():
    db = SessionLocal()
    try:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == g.user_id).first()
        if not profile:
            # Initialize a default profile for the user
            profile = StudentProfile(
                user_id=g.user_id,
                roll_number=f"STU{g.user_id:04d}",
                department_code="CS",
                cgpa=7.8,
                backlogs=0,
                internships_count=1,
                projects_count=2,
                certifications_count=1,
                coding_score=75.0,
                communication_score=80.0
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

        profile_dict = profile.to_dict()
        profile_dict["full_name"] = g.current_user.full_name or g.current_user.username
        profile_dict["email"] = g.current_user.email
        return jsonify({"profile": profile_dict}), 200

    except Exception as e:
        return jsonify({"error": "Failed to fetch profile", "detail": str(e)}), 500
    finally:
        db.close()

@students_bp.route("/profile", methods=["PUT"])
@login_required
def update_student_profile():
    data = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == g.user_id).first()
        if not profile:
            profile = StudentProfile(user_id=g.user_id)
            db.add(profile)

        # Validation
        if "roll_number" in data:
            profile.roll_number = str(data["roll_number"]).strip()
        
        if "department_code" in data:
            dept = str(data["department_code"]).strip().upper()
            if dept in ("CS", "AI", "EC", "ME", "EE", "CE"):
                profile.department_code = dept

        if "cgpa" in data:
            try:
                cgpa_val = float(data["cgpa"])
                if 0.0 <= cgpa_val <= 10.0:
                    profile.cgpa = round(cgpa_val, 2)
                else:
                    return jsonify({"error": "Validation Error", "detail": "CGPA must be between 0.0 and 10.0"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Validation Error", "detail": "Invalid numeric value for CGPA"}), 400

        if "backlogs" in data:
            try:
                b_val = int(data["backlogs"])
                if 0 <= b_val <= 30:
                    profile.backlogs = b_val
                else:
                    return jsonify({"error": "Validation Error", "detail": "Backlogs must be between 0 and 30"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Validation Error", "detail": "Invalid integer value for backlogs"}), 400

        if "internships_count" in data:
            profile.internships_count = max(0, int(data["internships_count"]))

        if "projects_count" in data:
            profile.projects_count = max(0, int(data["projects_count"]))

        if "certifications_count" in data:
            profile.certifications_count = max(0, int(data["certifications_count"]))

        if "coding_score" in data:
            c_val = float(data["coding_score"])
            profile.coding_score = round(min(max(c_val, 0.0), 100.0), 1)

        if "communication_score" in data:
            comm_val = float(data["communication_score"])
            profile.communication_score = round(min(max(comm_val, 0.0), 100.0), 1)

        profile.updated_at = datetime.datetime.utcnow()

        # Optionally update full_name on User model
        if "full_name" in data and data["full_name"]:
            user = db.query(User).filter(User.id == g.user_id).first()
            if user:
                user.full_name = str(data["full_name"]).strip()

        db.commit()
        db.refresh(profile)

        profile_dict = profile.to_dict()
        profile_dict["full_name"] = g.current_user.full_name or g.current_user.username
        profile_dict["email"] = g.current_user.email

        return jsonify({
            "message": "Student profile updated successfully",
            "profile": profile_dict
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to update profile", "detail": str(e)}), 500
    finally:
        db.close()

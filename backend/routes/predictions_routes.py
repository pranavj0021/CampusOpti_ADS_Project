import json
from flask import Blueprint, request, jsonify, g
from database import SessionLocal
from models.schemas_db import PredictionRecord, StudentProfile, User
from services.auth_service import login_required
from services.ml_service import ml_service

predictions_bp = Blueprint("predictions", __name__, url_prefix="/api/predictions")

@predictions_bp.route("", methods=["POST"])
@login_required
def create_prediction():
    data = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        # Fetch current user profile to autofill any omitted fields
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == g.user_id).first()
        
        # Merge payload with student profile defaults
        cgpa = float(data.get("cgpa", profile.cgpa if profile else 7.5))
        backlogs = int(data.get("backlogs", profile.backlogs if profile else 0))
        internships = int(data.get("internships", profile.internships_count if profile else 1))
        projects = int(data.get("projects", profile.projects_count if profile else 2))
        coding_score = float(data.get("coding_score", profile.coding_score if profile else 75.0))
        communication_score = float(data.get("communication_score", profile.communication_score if profile else 80.0))
        dept_code = str(data.get("department_code", profile.department_code if profile else "CS")).upper()
        model_name = str(data.get("model_name", "XGBoost"))
        student_name = str(data.get("student_name", g.current_user.full_name or g.current_user.username))
        roll_number = str(data.get("roll_number", profile.roll_number if profile else f"STU{g.user_id:04d}"))

        # Input validation
        if not (0.0 <= cgpa <= 10.0):
            return jsonify({"error": "Validation Error", "detail": "CGPA must be between 0.0 and 10.0"}), 400
        if backlogs < 0:
            return jsonify({"error": "Validation Error", "detail": "Backlogs cannot be negative"}), 400

        # Execute ML prediction
        input_payload = {
            "cgpa": cgpa,
            "backlogs": backlogs,
            "internships": internships,
            "projects": projects,
            "coding_score": coding_score,
            "communication_score": communication_score,
            "department_code": dept_code
        }
        pred_result = ml_service.predict_placement(input_payload, model_name=model_name)
        if "error" in pred_result:
            return jsonify({"error": "Prediction Error", "detail": pred_result["error"]}), 400

        # Persist prediction in database
        rec_text = json.dumps({
            "key_factors": pred_result.get("key_factors", []),
            "recommendations": pred_result.get("recommendations", [])
        })

        prediction_record = PredictionRecord(
            user_id=g.user_id,
            student_name=student_name,
            roll_number=roll_number,
            department_code=dept_code,
            cgpa=cgpa,
            backlogs=backlogs,
            internships=internships,
            projects=projects,
            coding_score=coding_score,
            communication_score=communication_score,
            predicted_status=pred_result["predicted_status"],
            placement_probability=pred_result["placement_probability"],
            risk_level=pred_result["risk_level"],
            model_used=pred_result["model_used"],
            recommendations=rec_text
        )
        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)

        response_dict = prediction_record.to_dict()
        response_dict["key_factors"] = pred_result.get("key_factors", [])
        response_dict["recommendations_list"] = pred_result.get("recommendations", [])

        return jsonify({
            "message": "Prediction generated and saved successfully",
            "prediction": response_dict
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Prediction Generation Failed", "detail": str(e)}), 500
    finally:
        db.close()

@predictions_bp.route("/history", methods=["GET"])
@login_required
def get_prediction_history():
    db = SessionLocal()
    try:
        # Authorization check:
        # Admins can view all predictions or filter by user; regular users can only see their own
        query = db.query(PredictionRecord)
        if g.role != "admin":
            query = query.filter(PredictionRecord.user_id == g.user_id)
        else:
            user_filter = request.args.get("user_id")
            if user_filter:
                query = query.filter(PredictionRecord.user_id == int(user_filter))

        records = query.order_by(PredictionRecord.created_at.desc()).all()
        results = []
        for r in records:
            d = r.to_dict()
            try:
                parsed_rec = json.loads(r.recommendations) if r.recommendations else {}
                d["recommendations_list"] = parsed_rec.get("recommendations", [])
                d["key_factors"] = parsed_rec.get("key_factors", [])
            except Exception:
                d["recommendations_list"] = [r.recommendations] if r.recommendations else []
                d["key_factors"] = []
            results.append(d)

        return jsonify({
            "total_records": len(results),
            "history": results
        }), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve history", "detail": str(e)}), 500
    finally:
        db.close()

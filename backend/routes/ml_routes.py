from flask import Blueprint, request, jsonify, g
from database import SessionLocal
from services.auth_service import login_required
from services.ml_service import ml_service

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")

@ml_bp.route("/models", methods=["GET"])
def get_models():
    placement_info = ml_service.get_placement_model_info()
    campus_info = ml_service.get_campus_evaluations()
    return jsonify({
        "placement_models": {
            "candidate_models": placement_info.get("available_models", ["XGBoost", "RandomForest", "LogisticRegression"]),
            "best_model": placement_info.get("best_model", "XGBoost"),
            "features": placement_info.get("feature_names", [])
        },
        "campus_forecast_models": {
            "candidate_models": ["LinearRegression", "RandomForest", "XGBoost"],
            "best_model": campus_info.get("best_model", "XGBoost"),
            "features": campus_info.get("features", [])
        }
    }), 200

@ml_bp.route("/evaluations", methods=["GET"])
def get_evaluations():
    placement_info = ml_service.get_placement_model_info()
    campus_info = ml_service.get_campus_evaluations()
    return jsonify({
        "placement_metrics": placement_info.get("metrics", {}),
        "campus_forecast_metrics": campus_info.get("evaluations", {}),
        "validation_strategy": "Chronological hold-out validation (Campus) and Stratified Hold-Out (Placement)"
    }), 200

@ml_bp.route("/predict/enrollment", methods=["POST"])
@login_required
def predict_enrollment():
    data = request.get_json(silent=True) or {}
    academic_year = str(data.get("academic_year", "2026-2027"))
    model_name = str(data.get("model_name", "XGBoost"))

    db = SessionLocal()
    try:
        result = ml_service.predict_enrollment(academic_year, db, model_name=model_name)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Enrollment forecasting failed", "detail": str(e)}), 500
    finally:
        db.close()

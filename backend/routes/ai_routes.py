from flask import Blueprint, request, jsonify, g
from database import SessionLocal
from services.auth_service import login_required
from services.ai_service import ai_service

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

@ai_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    academic_year = str(data.get("academic_year", "2026-2027"))

    if not message:
        return jsonify({"error": "Validation Error", "detail": "Message query cannot be empty"}), 400

    db = SessionLocal()
    try:
        reply_data = ai_service.generate_reply(
            message=message,
            user_id=g.user_id,
            db=db,
            academic_year=academic_year
        )
        return jsonify(reply_data), 200
    except Exception as e:
        return jsonify({"error": "AI Advisor Failure", "detail": str(e)}), 500
    finally:
        db.close()

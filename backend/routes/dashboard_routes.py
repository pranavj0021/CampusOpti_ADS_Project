from flask import Blueprint, request, jsonify, g
from database import SessionLocal
from models.schemas_db import Department, Classroom, Faculty, Laboratory, Equipment, StudentEnrollment
from services.auth_service import login_required
from services.ml_service import ml_service

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

@dashboard_bp.route("/departments", methods=["GET"])
def get_departments():
    db = SessionLocal()
    try:
        departments = db.query(Department).all()
        return jsonify([d.to_dict() for d in departments]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch departments", "detail": str(e)}), 500
    finally:
        db.close()

@dashboard_bp.route("/overview", methods=["GET"])
@login_required
def get_dashboard_overview():
    academic_year = request.args.get("academic_year", "2026-2027")
    db = SessionLocal()
    try:
        # Run ML forecast for selected year
        forecast = ml_service.predict_enrollment(academic_year, db)

        # Count resource assets
        total_classrooms = db.query(Classroom).filter(Classroom.is_available == True).count()
        total_faculty = db.query(Faculty).filter(Faculty.is_available == True).count()
        labs = db.query(Laboratory).all()
        equipments = db.query(Equipment).all()

        total_eq = sum(e.quantity for e in equipments)
        op_eq = sum(e.operational_count for e in equipments)
        avg_lab_util = round(sum(l.current_utilization for l in labs) / max(1, len(labs)), 1) if labs else 75.0

        # Department breakdown
        depts = db.query(Department).all()
        dept_summaries = []
        for d in depts:
            f_info = next((f for f in forecast["department_forecasts"] if f["department_code"] == d.code), None)
            proj_students = f_info["predicted_students"] if f_info else 250
            growth = f_info["growth_rate_pct"] if f_info else 5.0
            dept_summaries.append({
                "code": d.code,
                "name": d.name,
                "building": d.building,
                "projected_students": proj_students,
                "growth_rate": growth,
                "status": "Optimal" if growth < 6.0 else "High Growth"
            })

        return jsonify({
            "academic_year": academic_year,
            "kpis": {
                "total_predicted_students": forecast["total_predicted_students"],
                "available_classrooms": total_classrooms,
                "available_faculty": total_faculty,
                "laboratories_count": len(labs),
                "avg_lab_utilization": avg_lab_util,
                "equipment_operational": op_eq,
                "equipment_total": total_eq
            },
            "department_forecasts": forecast["department_forecasts"],
            "department_summaries": dept_summaries
        }), 200

    except Exception as e:
        return jsonify({"error": "Failed to generate dashboard overview", "detail": str(e)}), 500
    finally:
        db.close()

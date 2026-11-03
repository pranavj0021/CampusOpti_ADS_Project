from flask import Blueprint, jsonify, g
from sqlalchemy import func
from database import SessionLocal
from models.schemas_db import (
    User, StudentProfile, PredictionRecord, Department, StudentEnrollment,
    Classroom, Faculty, Laboratory, Equipment
)
from services.auth_service import login_required
from services.ml_service import ml_service

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@analytics_bp.route("", methods=["GET"])
@login_required
def get_analytics():
    db = SessionLocal()
    try:
        # 1. User & Student Counts
        total_users = db.query(User).count()
        total_students = db.query(User).filter(User.role == "student").count()
        total_profiles = db.query(StudentProfile).count()

        # 2. Placement Predictions Aggregates
        predictions = db.query(PredictionRecord).all()
        total_preds = len(predictions)
        avg_prob = 0.0
        status_dist = {"High Chance": 0, "Moderate Chance": 0, "Needs Improvement": 0}
        risk_dist = {"Low Risk": 0, "Moderate Risk": 0, "High Risk": 0}
        dept_preds = {}

        if total_preds > 0:
            avg_prob = round(sum(p.placement_probability for p in predictions) / total_preds * 100, 1)
            for p in predictions:
                status_dist[p.predicted_status] = status_dist.get(p.predicted_status, 0) + 1
                risk_dist[p.risk_level] = risk_dist.get(p.risk_level, 0) + 1
                
                dept = p.department_code or "Unknown"
                dept_preds.setdefault(dept, []).append(p.placement_probability)

        dept_avg_readiness = [
            {
                "department": dept,
                "count": len(probs),
                "avg_placement_pct": round(sum(probs) / len(probs) * 100, 1)
            }
            for dept, probs in dept_preds.items()
        ]

        # 3. Student Academic Benchmarks
        profiles = db.query(StudentProfile).all()
        avg_cgpa = round(sum(p.cgpa for p in profiles) / max(1, len(profiles)), 2) if profiles else 7.5
        avg_coding = round(sum(p.coding_score for p in profiles) / max(1, len(profiles)), 1) if profiles else 75.0
        avg_comm = round(sum(p.communication_score for p in profiles) / max(1, len(profiles)), 1) if profiles else 80.0

        # 4. Department Enrollment Totals
        departments = db.query(Department).all()
        dept_enrollments = []
        for d in departments:
            enrollments = db.query(StudentEnrollment).filter(StudentEnrollment.department_code == d.code).all()
            total_students_dept = sum(e.total_students for e in enrollments)
            dept_enrollments.append({
                "code": d.code,
                "name": d.name,
                "building": d.building,
                "total_historical_students": total_students_dept
            })

        # 5. Campus Infrastructure Capacity
        classrooms = db.query(Classroom).all()
        total_classrooms = len(classrooms)
        avg_classroom_util = round(sum(c.current_utilization for c in classrooms) / max(1, total_classrooms), 1) if classrooms else 75.0

        faculty_members = db.query(Faculty).all()
        total_faculty = len(faculty_members)
        avg_teaching_hours = round(sum(f.current_teaching_hours for f in faculty_members) / max(1, total_faculty), 1) if faculty_members else 14.0

        labs = db.query(Laboratory).all()
        total_labs = len(labs)
        total_computers = sum(l.computers_count for l in labs)

        equipments = db.query(Equipment).all()
        total_equipment_units = sum(e.quantity for e in equipments)
        operational_equipment = sum(e.operational_count for e in equipments)

        # 6. ML Model Information
        placement_models_info = ml_service.get_placement_model_info()

        return jsonify({
            "overview": {
                "total_users": total_users,
                "total_students": total_students,
                "total_profiles": total_profiles,
                "total_predictions": total_preds,
                "average_placement_rate_pct": avg_prob,
                "benchmark_cgpa": avg_cgpa,
                "benchmark_coding_score": avg_coding,
                "benchmark_comm_score": avg_comm
            },
            "placement_analytics": {
                "status_distribution": status_dist,
                "risk_distribution": risk_dist,
                "department_readiness": dept_avg_readiness,
                "models_evaluation": placement_models_info.get("metrics", {})
            },
            "campus_infrastructure": {
                "total_departments": len(departments),
                "total_classrooms": total_classrooms,
                "avg_classroom_utilization": avg_classroom_util,
                "total_faculty": total_faculty,
                "avg_teaching_hours": avg_teaching_hours,
                "total_laboratories": total_labs,
                "total_computers": total_computers,
                "total_equipment_units": total_equipment_units,
                "operational_equipment_units": operational_equipment,
                "departments": dept_enrollments
            }
        }), 200

    except Exception as e:
        return jsonify({"error": "Failed to calculate analytics", "detail": str(e)}), 500
    finally:
        db.close()

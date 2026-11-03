import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.schemas_db import (
    Classroom, Faculty, Laboratory, Equipment, Department, 
    StudentEnrollment, ResourceGapAnalysis
)
from app.ml.pipeline import ml_pipeline

class ResourceGapEngine:
    """
    Core engine for computing academic resource demand, identifying shortages/surpluses,
    calculating priority scores, and generating actionable management recommendations.
    """
    
    # Configurable Institutional Benchmark Standards
    DEFAULT_CLASSROOM_CAPACITY = 60
    TARGET_ROOM_UTILIZATION = 0.80  # 80% optimal room utilization
    ROOM_SHIFTS_PER_DAY = 1.35      # Staggered lecture schedules factor
    
    STUDENT_FACULTY_RATIO_TARGET = 18.0  # 1 faculty per 18 students
    FACULTY_MAX_WEEKLY_HOURS = 16.0
    
    LAB_BATCH_SIZE = 30
    LAB_HOURS_PER_WEEK_PER_STUDENT = 3.5
    LAB_OPERATING_HOURS_PER_WEEK = 35.0  # 7 hours x 5 days
    
    EQUIPMENT_STUDENT_RATIO_CS_AI = 0.90  # 90% 1-to-1 computer workstation ratio
    EQUIPMENT_STUDENT_RATIO_OTHER = 0.35  # Specialized test rigs/kits shared in small groups

    # Department academic criticality weights (0.0 to 1.0)
    DEPT_CRITICALITY = {
        "CS": 0.95,
        "AI": 1.00,
        "EC": 0.85,
        "EE": 0.80,
        "ME": 0.75,
        "CE": 0.70
    }

    @classmethod
    def calculate_gaps(
        cls, 
        academic_year: str, 
        db: Session,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete resource gap analysis for all departments for target academic year.
        """
        # 1. Obtain projected enrollments from ML forecast engine
        forecast_res = ml_pipeline.predict_enrollment(
            target_academic_year=academic_year, 
            db=db, 
            model_name=model_name
        )
        dept_forecasts = {f["department_code"]: f for f in forecast_res["department_forecasts"]}

        # 2. Gather currently available resources from database
        all_classrooms = db.query(Classroom).all()
        all_faculty = db.query(Faculty).all()
        all_labs = db.query(Laboratory).all()
        all_equipment = db.query(Equipment).all()
        departments = db.query(Department).all()

        gap_items: List[Dict[str, Any]] = []
        recommendations: List[Dict[str, Any]] = []
        rec_id_counter = 1

        summary_by_category = {
            "Classrooms": {"required": 0, "available": 0, "gap": 0},
            "Faculty": {"required": 0, "available": 0, "gap": 0},
            "Laboratories": {"required": 0, "available": 0, "gap": 0},
            "Equipment": {"required": 0, "available": 0, "gap": 0}
        }

        total_shortages = 0
        total_surpluses = 0

        # Process each department
        for dept in departments:
            code = dept.code
            forecast_info = dept_forecasts.get(code, {
                "predicted_students": 300,
                "growth_rate_pct": 5.0
            })
            predicted_students = max(10, forecast_info["predicted_students"])
            growth_pct = forecast_info["growth_rate_pct"]
            criticality = cls.DEPT_CRITICALITY.get(code, 0.80)

            # --- A. Classroom Demand & Gap ---
            dept_rooms = [r for r in all_classrooms if r.department_code == code and r.is_available]
            available_rooms = len(dept_rooms)
            avg_utilization_rooms = sum(r.current_utilization for r in dept_rooms) / max(1, available_rooms) if dept_rooms else 75.0

            # Demand Formula: ceil(predicted_students / (avg_capacity * utilization * shifts))
            effective_room_capacity = cls.DEFAULT_CLASSROOM_CAPACITY * cls.TARGET_ROOM_UTILIZATION * cls.ROOM_SHIFTS_PER_DAY
            required_rooms = max(1, math.ceil(predicted_students / max(1, effective_room_capacity)))
            room_gap = round(required_rooms - available_rooms, 1)

            room_priority = cls._calculate_priority_score(
                gap=room_gap,
                utilization=avg_utilization_rooms,
                growth_rate=growth_pct,
                criticality=criticality
            )

            status_room = "Shortage" if room_gap > 0 else ("Surplus" if room_gap < 0 else "Balanced")
            if room_gap > 0:
                total_shortages += 1
            elif room_gap < 0:
                total_surpluses += 1

            room_rec_text = (
                f"Allocate {int(room_gap)} additional smart classrooms for {dept.name} to accommodate "
                f"projected enrollment of {predicted_students} students."
                if room_gap > 0 else (
                    f"{dept.name} has {abs(int(room_gap))} surplus lecture rooms; consider reallocating to high-growth departments."
                    if room_gap < 0 else f"{dept.name} classroom capacity is currently balanced."
                )
            )

            gap_items.append({
                "department_code": code,
                "resource_category": "Classrooms",
                "required_quantity": float(required_rooms),
                "available_quantity": float(available_rooms),
                "gap_quantity": float(room_gap),
                "utilization_rate": round(avg_utilization_rooms, 1),
                "priority_score": round(room_priority, 1),
                "status": status_room,
                "urgency": cls._get_urgency(room_priority, room_gap),
                "recommendation": room_rec_text
            })

            summary_by_category["Classrooms"]["required"] += required_rooms
            summary_by_category["Classrooms"]["available"] += available_rooms
            summary_by_category["Classrooms"]["gap"] += room_gap

            if room_gap > 0:
                recommendations.append({
                    "id": f"REC-{rec_id_counter:03d}",
                    "department": code,
                    "resource_type": "Classrooms",
                    "action_type": "Add Classrooms",
                    "recommended_quantity": int(room_gap),
                    "priority_score": round(room_priority, 1),
                    "severity": cls._get_urgency(room_priority, room_gap),
                    "reason": f"Projected enrollment growth of {growth_pct}% exceeds currently assigned {available_rooms} classrooms.",
                    "formula_explanation": f"Demand = ceil({predicted_students} / ({cls.DEFAULT_CLASSROOM_CAPACITY} * {cls.TARGET_ROOM_UTILIZATION} * {cls.ROOM_SHIFTS_PER_DAY})) = {required_rooms} rooms."
                })
                rec_id_counter += 1

            # --- B. Faculty Demand & Gap ---
            dept_faculty = [f for f in all_faculty if f.department_code == code and f.is_available]
            available_faculty = len(dept_faculty)
            avg_faculty_hours = sum(f.current_teaching_hours for f in dept_faculty) / max(1, available_faculty) if dept_faculty else 14.0
            faculty_utilization = min(100.0, (avg_faculty_hours / cls.FACULTY_MAX_WEEKLY_HOURS) * 100.0)

            # Demand: max(ceil(students / ratio), ceil(teaching_hours / max_workload))
            faculty_demand_by_ratio = math.ceil(predicted_students / cls.STUDENT_FACULTY_RATIO_TARGET)
            required_faculty = max(2, faculty_demand_by_ratio)
            faculty_gap = round(required_faculty - available_faculty, 1)

            faculty_priority = cls._calculate_priority_score(
                gap=faculty_gap,
                utilization=faculty_utilization,
                growth_rate=growth_pct,
                criticality=criticality
            )

            status_faculty = "Shortage" if faculty_gap > 0 else ("Surplus" if faculty_gap < 0 else "Balanced")
            if faculty_gap > 0:
                total_shortages += 1
            elif faculty_gap < 0:
                total_surpluses += 1

            gap_items.append({
                "department_code": code,
                "resource_category": "Faculty",
                "required_quantity": float(required_faculty),
                "available_quantity": float(available_faculty),
                "gap_quantity": float(faculty_gap),
                "utilization_rate": round(faculty_utilization, 1),
                "priority_score": round(faculty_priority, 1),
                "status": status_faculty,
                "urgency": cls._get_urgency(faculty_priority, faculty_gap),
                "recommendation": (
                    f"Recruit {int(faculty_gap)} professors/lecturers in {code} to maintain 1:{int(cls.STUDENT_FACULTY_RATIO_TARGET)} student-faculty ratio."
                    if faculty_gap > 0 else f"{code} faculty strength is optimal."
                )
            })

            summary_by_category["Faculty"]["required"] += required_faculty
            summary_by_category["Faculty"]["available"] += available_faculty
            summary_by_category["Faculty"]["gap"] += faculty_gap

            if faculty_gap > 0:
                recommendations.append({
                    "id": f"REC-{rec_id_counter:03d}",
                    "department": code,
                    "resource_type": "Faculty",
                    "action_type": "Recruit Faculty",
                    "recommended_quantity": int(faculty_gap),
                    "priority_score": round(faculty_priority, 1),
                    "severity": cls._get_urgency(faculty_priority, faculty_gap),
                    "reason": f"Current faculty count ({available_faculty}) yields an unfeasible student-to-faculty ratio of 1:{round(predicted_students/max(1, available_faculty), 1)}.",
                    "formula_explanation": f"Demand = ceil({predicted_students} / {cls.STUDENT_FACULTY_RATIO_TARGET}) = {required_faculty} faculty."
                })
                rec_id_counter += 1

            # --- C. Laboratory Demand & Gap ---
            dept_labs = [l for l in all_labs if l.department_code == code and l.is_available]
            available_labs = len(dept_labs)
            avg_lab_utilization = sum(l.current_utilization for l in dept_labs) / max(1, available_labs) if dept_labs else 70.0

            # Required labs = ceil((predicted_students * weekly_lab_hours) / (batch_size * operating_hours))
            total_weekly_practical_hours = predicted_students * cls.LAB_HOURS_PER_WEEK_PER_STUDENT
            lab_capacity_per_week = cls.LAB_BATCH_SIZE * cls.LAB_OPERATING_HOURS_PER_WEEK
            required_labs = max(1, math.ceil(total_weekly_practical_hours / max(1, lab_capacity_per_week)))
            lab_gap = round(required_labs - available_labs, 1)

            lab_priority = cls._calculate_priority_score(
                gap=lab_gap,
                utilization=avg_lab_utilization,
                growth_rate=growth_pct,
                criticality=criticality
            )

            status_lab = "Shortage" if lab_gap > 0 else ("Surplus" if lab_gap < 0 else "Balanced")
            if lab_gap > 0:
                total_shortages += 1
            elif lab_gap < 0:
                total_surpluses += 1

            gap_items.append({
                "department_code": code,
                "resource_category": "Laboratories",
                "required_quantity": float(required_labs),
                "available_quantity": float(available_labs),
                "gap_quantity": float(lab_gap),
                "utilization_rate": round(avg_lab_utilization, 1),
                "priority_score": round(lab_priority, 1),
                "status": status_lab,
                "urgency": cls._get_urgency(lab_priority, lab_gap),
                "recommendation": (
                    f"Commission {int(lab_gap)} additional specialized lab section(s) or add evening batch shifts for {code}."
                    if lab_gap > 0 else f"{code} lab infrastructure is adequate."
                )
            })

            summary_by_category["Laboratories"]["required"] += required_labs
            summary_by_category["Laboratories"]["available"] += available_labs
            summary_by_category["Laboratories"]["gap"] += lab_gap

            if lab_gap > 0:
                recommendations.append({
                    "id": f"REC-{rec_id_counter:03d}",
                    "department": code,
                    "resource_type": "Laboratories",
                    "action_type": "Increase Lab Capacity",
                    "recommended_quantity": int(lab_gap),
                    "priority_score": round(lab_priority, 1),
                    "severity": cls._get_urgency(lab_priority, lab_gap),
                    "reason": f"Practical training load exceeds current {available_labs} laboratory capacities during peak hours.",
                    "formula_explanation": f"Demand = ceil(({predicted_students} * {cls.LAB_HOURS_PER_WEEK_PER_STUDENT}) / ({cls.LAB_BATCH_SIZE} * {cls.LAB_OPERATING_HOURS_PER_WEEK})) = {required_labs} labs."
                })
                rec_id_counter += 1

            # --- D. Equipment Demand & Gap ---
            dept_equipment = [e for e in all_equipment if e.department_code == code]
            available_equipment = sum(e.operational_count for e in dept_equipment)
            maintenance_count = sum(e.maintenance_count for e in dept_equipment)
            total_inv = sum(e.quantity for e in dept_equipment)
            equip_utilization = min(100.0, (available_equipment / max(1, total_inv)) * 100.0)

            ratio = cls.EQUIPMENT_STUDENT_RATIO_CS_AI if code in ["CS", "AI"] else cls.EQUIPMENT_STUDENT_RATIO_OTHER
            # Estimate required units: based on simultaneous batch lab sizes
            simultaneous_lab_students = math.ceil(predicted_students * 0.25)
            required_equipment = max(10, int(simultaneous_lab_students * (1.0 if code in ["CS", "AI"] else 0.5)))
            equip_gap = round(required_equipment - available_equipment, 1)

            equip_priority = cls._calculate_priority_score(
                gap=equip_gap,
                utilization=equip_utilization,
                growth_rate=growth_pct,
                criticality=criticality
            )

            status_equip = "Shortage" if equip_gap > 0 else ("Surplus" if equip_gap < 0 else "Balanced")
            if equip_gap > 0:
                total_shortages += 1
            elif equip_gap < 0:
                total_surpluses += 1

            gap_items.append({
                "department_code": code,
                "resource_category": "Equipment",
                "required_quantity": float(required_equipment),
                "available_quantity": float(available_equipment),
                "gap_quantity": float(equip_gap),
                "utilization_rate": round(equip_utilization, 1),
                "priority_score": round(equip_priority, 1),
                "status": status_equip,
                "urgency": cls._get_urgency(equip_priority, equip_gap),
                "recommendation": (
                    f"Procure {int(equip_gap)} additional units and repair {maintenance_count} offline units for {code}."
                    if equip_gap > 0 else f"{code} equipment inventory is sufficient."
                )
            })

            summary_by_category["Equipment"]["required"] += required_equipment
            summary_by_category["Equipment"]["available"] += available_equipment
            summary_by_category["Equipment"]["gap"] += equip_gap

            if equip_gap > 0:
                recommendations.append({
                    "id": f"REC-{rec_id_counter:03d}",
                    "department": code,
                    "resource_type": "Equipment",
                    "action_type": "Purchase Equipment",
                    "recommended_quantity": int(equip_gap),
                    "priority_score": round(equip_priority, 1),
                    "severity": cls._get_urgency(equip_priority, equip_gap),
                    "reason": f"Operational equipment inventory ({available_equipment}) fails to meet 1:1 simultaneous lab session demands.",
                    "formula_explanation": f"Demand = simultaneous lab students ({simultaneous_lab_students}) * unit_ratio = {required_equipment} units."
                })
                rec_id_counter += 1

            # Check for maintenance repair recommendation
            if maintenance_count > 0:
                recommendations.append({
                    "id": f"REC-{rec_id_counter:03d}",
                    "department": code,
                    "resource_type": "Equipment",
                    "action_type": "Repair Equipment",
                    "recommended_quantity": int(maintenance_count),
                    "priority_score": 68.0,
                    "severity": "Medium",
                    "reason": f"{maintenance_count} equipment units are currently offline for maintenance.",
                    "formula_explanation": "Expedited servicing will recover immediate capacity without new procurement capital."
                })
                rec_id_counter += 1

        # Check for cross-department redistribution opportunities (Surplus -> Shortage)
        surplus_rooms = [g for g in gap_items if g["resource_category"] == "Classrooms" and g["gap_quantity"] < -0.5]
        shortage_rooms = [g for g in gap_items if g["resource_category"] == "Classrooms" and g["gap_quantity"] > 0]
        if surplus_rooms and shortage_rooms:
            donor = surplus_rooms[0]["department_code"]
            recipient = shortage_rooms[0]["department_code"]
            qty = min(abs(int(surplus_rooms[0]["gap_quantity"])), int(shortage_rooms[0]["gap_quantity"]))
            if qty > 0:
                recommendations.append({
                    "id": f"REC-{rec_id_counter:03d}",
                    "department": f"{donor} -> {recipient}",
                    "resource_type": "Classrooms",
                    "action_type": "Redistribute Resources",
                    "recommended_quantity": qty,
                    "priority_score": 82.5,
                    "severity": "High",
                    "reason": f"Underutilized classrooms in {donor} can be scheduled for {recipient} morning lectures.",
                    "formula_explanation": f"Redistribution saves capital expenditure by leveling inter-departmental utilization gaps."
                })
                rec_id_counter += 1

        # Sort recommendations by priority score descending
        recommendations.sort(key=lambda r: r["priority_score"], reverse=True)

        # Calculate overall institutional health score (0 - 100)
        overall_health = max(40.0, 100.0 - (total_shortages * 4.5))

        return {
            "academic_year": academic_year,
            "total_shortages": total_shortages,
            "total_surpluses": total_surpluses,
            "overall_health_score": round(overall_health, 1),
            "items": gap_items,
            "recommendations": recommendations,
            "summary_by_category": summary_by_category
        }

    @staticmethod
    def _calculate_priority_score(gap: float, utilization: float, growth_rate: float, criticality: float) -> float:
        """
        Priority Score Formula:
        Score = (Normalized Shortage Severity * 0.40) + 
                (Utilization * 0.25) + 
                (Normalized Growth * 0.20) + 
                (Academic Criticality * 0.15)
        Scale: 0 to 100
        """
        # If surplus (negative gap), priority is lower
        if gap <= 0:
            severity_component = max(0.0, 30.0 - abs(gap) * 5.0)
        else:
            severity_component = min(100.0, gap * 20.0 + 35.0)

        utilization_component = min(100.0, max(0.0, utilization))
        growth_component = min(100.0, max(0.0, growth_rate * 3.5))
        criticality_component = criticality * 100.0

        score = (
            (severity_component * 0.40) +
            (utilization_component * 0.25) +
            (growth_component * 0.20) +
            (criticality_component * 0.15)
        )
        return min(99.0, max(10.0, score))

    @staticmethod
    def _get_urgency(score: float, gap: float) -> str:
        if gap <= 0:
            return "Low"
        if score >= 80.0:
            return "Critical"
        if score >= 65.0:
            return "High"
        if score >= 45.0:
            return "Medium"
        return "Low"

import io
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.schemas_db import (
    StudentEnrollment, Classroom, Faculty, Laboratory, 
    Equipment, Course, AcademicCalendar, DatasetImport
)
from app.ml.pipeline import ml_pipeline

class DataIngestionService:
    REQUIRED_COLUMNS = {
        "students": ["department_code", "academic_year", "total_students"],
        "classrooms": ["room_id", "department_code", "capacity"],
        "faculty": ["faculty_id", "name", "department_code"],
        "laboratories": ["lab_id", "lab_name", "department_code", "capacity"],
        "equipment": ["equipment_id", "name", "equipment_type", "department_code", "quantity"],
        "courses": ["course_id", "course_name", "department_code"],
        "academic_calendar": ["academic_year", "semester"]
    }

    @classmethod
    async def process_file(
        cls, 
        file: UploadFile, 
        entity_type: str, 
        db: Session
    ) -> Dict[str, Any]:
        filename = file.filename
        content = await file.read()

        # Parse dataframe based on extension
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(content))
            else:
                return {
                    "filename": filename,
                    "entity_type": entity_type,
                    "total_rows": 0,
                    "accepted_rows": 0,
                    "rejected_rows": 0,
                    "status": "Failed",
                    "warnings": ["Unsupported file format. Please upload CSV or Excel."],
                    "errors": [{"row": 0, "column": "format", "value": filename, "error": "Invalid file type"}]
                }
        except Exception as e:
            return {
                "filename": filename,
                "entity_type": entity_type,
                "total_rows": 0,
                "accepted_rows": 0,
                "rejected_rows": 0,
                "status": "Failed",
                "warnings": [f"File parsing error: {str(e)}"],
                "errors": [{"row": 0, "column": "file", "value": None, "error": str(e)}]
            }

        # Check required columns
        req_cols = cls.REQUIRED_COLUMNS.get(entity_type.lower(), [])
        missing_headers = [c for c in req_cols if c not in df.columns]
        if missing_headers:
            return {
                "filename": filename,
                "entity_type": entity_type,
                "total_rows": len(df),
                "accepted_rows": 0,
                "rejected_rows": len(df),
                "status": "Failed",
                "warnings": [f"Missing required columns: {', '.join(missing_headers)}"],
                "errors": [{"row": 0, "column": "headers", "value": None, "error": f"Missing: {missing_headers}"}]
            }

        total_rows = len(df)
        accepted_rows = 0
        rejected_rows = 0
        errors: List[Dict[str, Any]] = []
        warnings: List[str] = []

        # Duplicate detection within file
        id_col = "room_id" if entity_type == "classrooms" else (
            "faculty_id" if entity_type == "faculty" else (
                "lab_id" if entity_type == "laboratories" else (
                    "equipment_id" if entity_type == "equipment" else (
                        "course_id" if entity_type == "courses" else None
                    )
                )
            )
        )

        seen_ids = set()
        accepted_records = []

        for idx, row in df.iterrows():
            row_idx = idx + 2 # 1-indexed Excel header offset
            row_dict = row.to_dict()

            # Check for empty critical values
            has_nan = False
            for col in req_cols:
                val = row_dict.get(col)
                if pd.isna(val) or str(val).strip() == "":
                    errors.append({
                        "row": row_idx,
                        "column": col,
                        "value": str(val),
                        "error": "Missing required field value"
                    })
                    has_nan = True
                    break

            if has_nan:
                rejected_rows += 1
                continue

            # Duplicate ID check
            if id_col and id_col in row_dict:
                item_id = str(row_dict[id_col]).strip()
                if item_id in seen_ids:
                    errors.append({
                        "row": row_idx,
                        "column": id_col,
                        "value": item_id,
                        "error": f"Duplicate primary identifier '{item_id}' detected in uploaded batch"
                    })
                    rejected_rows += 1
                    continue
                seen_ids.add(item_id)

            # Domain validation & outlier detection per entity
            is_valid, err_msg = cls._validate_row(entity_type, row_dict)
            if not is_valid:
                errors.append({
                    "row": row_idx,
                    "column": err_msg.get("col"),
                    "value": err_msg.get("val"),
                    "error": err_msg.get("msg")
                })
                rejected_rows += 1
                continue

            # Save accepted
            accepted_records.append(row_dict)
            accepted_rows += 1

        # Commit accepted rows to database
        if accepted_records:
            cls._save_records_to_db(entity_type, accepted_records, db)

        status_str = "Success" if rejected_rows == 0 else ("Partial" if accepted_rows > 0 else "Failed")
        if rejected_rows > 0:
            warnings.append(f"{rejected_rows} rows were rejected due to data validation issues.")

        # Log import record in DB
        import_job = DatasetImport(
            filename=filename,
            entity_type=entity_type,
            total_rows=total_rows,
            accepted_rows=accepted_rows,
            rejected_rows=rejected_rows,
            validation_report={"warnings": warnings, "errors": errors[:50]},
            status=status_str
        )
        db.add(import_job)
        db.commit()

        # Trigger ML model retraining if student enrollments were imported
        if entity_type.lower() == "students" and accepted_rows > 0:
            try:
                ml_pipeline.train_from_db(db)
                warnings.append("Machine Learning forecasting model was successfully retrained with updated enrollment data.")
            except Exception as e:
                warnings.append(f"Model retrain notice: {str(e)}")

        return {
            "filename": filename,
            "entity_type": entity_type,
            "total_rows": total_rows,
            "accepted_rows": accepted_rows,
            "rejected_rows": rejected_rows,
            "status": status_str,
            "warnings": warnings,
            "errors": errors[:50]
        }

    @staticmethod
    def _validate_row(entity_type: str, row: Dict[str, Any]) -> (bool, Optional[Dict[str, Any]]):
        try:
            if entity_type == "students":
                count = int(row.get("total_students", 0))
                if count <= 0 or count > 5000:
                    return False, {"col": "total_students", "val": count, "msg": "Student count must be between 1 and 5000"}
            elif entity_type == "classrooms":
                cap = int(row.get("capacity", 0))
                if cap <= 0 or cap > 1000:
                    return False, {"col": "capacity", "val": cap, "msg": "Classroom capacity must be between 1 and 1000"}
                util = float(row.get("current_utilization", 75.0))
                if util < 0 or util > 100:
                    return False, {"col": "current_utilization", "val": util, "msg": "Utilization percentage must be between 0 and 100"}
            elif entity_type == "laboratories":
                cap = int(row.get("capacity", 0))
                if cap <= 0 or cap > 200:
                    return False, {"col": "capacity", "val": cap, "msg": "Laboratory capacity must be between 1 and 200"}
            elif entity_type == "equipment":
                qty = int(row.get("quantity", 0))
                if qty < 0:
                    return False, {"col": "quantity", "val": qty, "msg": "Quantity cannot be negative"}
            return True, None
        except Exception as e:
            return False, {"col": "general", "val": None, "msg": f"Type conversion error: {str(e)}"}

    @staticmethod
    def _save_records_to_db(entity_type: str, records: List[Dict[str, Any]], db: Session):
        for r in records:
            if entity_type == "students":
                rec = StudentEnrollment(
                    department_code=str(r["department_code"]).strip().upper(),
                    academic_year=str(r["academic_year"]).strip(),
                    year_level=int(r.get("year_level", 1)),
                    semester=str(r.get("semester", "Fall")).strip(),
                    program=str(r.get("program", "B.Tech")).strip(),
                    total_students=int(r["total_students"]),
                    divisions_count=int(r.get("divisions_count", 1))
                )
                db.add(rec)
            elif entity_type == "classrooms":
                existing = db.query(Classroom).filter(Classroom.room_id == str(r["room_id"])).first()
                if existing:
                    existing.capacity = int(r["capacity"])
                    existing.department_code = str(r["department_code"])
                    existing.current_utilization = float(r.get("current_utilization", 75.0))
                else:
                    db.add(Classroom(
                        room_id=str(r["room_id"]).strip(),
                        department_code=str(r["department_code"]).strip().upper(),
                        capacity=int(r["capacity"]),
                        room_type=str(r.get("room_type", "Lecture Hall")),
                        current_utilization=float(r.get("current_utilization", 75.0)),
                        is_available=bool(r.get("is_available", True)),
                        building_block=str(r.get("building_block", "Block A"))
                    ))
            elif entity_type == "faculty":
                existing = db.query(Faculty).filter(Faculty.faculty_id == str(r["faculty_id"])).first()
                if existing:
                    existing.name = str(r["name"])
                    existing.department_code = str(r["department_code"])
                else:
                    db.add(Faculty(
                        faculty_id=str(r["faculty_id"]).strip(),
                        name=str(r["name"]).strip(),
                        department_code=str(r["department_code"]).strip().upper(),
                        designation=str(r.get("designation", "Assistant Professor")),
                        specialization=str(r.get("specialization", "Engineering")),
                        current_teaching_hours=float(r.get("current_teaching_hours", 14.0)),
                        max_workload_hours=float(r.get("max_workload_hours", 16.0)),
                        is_available=bool(r.get("is_available", True))
                    ))
            elif entity_type == "laboratories":
                existing = db.query(Laboratory).filter(Laboratory.lab_id == str(r["lab_id"])).first()
                if existing:
                    existing.capacity = int(r["capacity"])
                else:
                    db.add(Laboratory(
                        lab_id=str(r["lab_id"]).strip(),
                        lab_name=str(r["lab_name"]).strip(),
                        department_code=str(r["department_code"]).strip().upper(),
                        capacity=int(r["capacity"]),
                        computers_count=int(r.get("computers_count", 30)),
                        current_utilization=float(r.get("current_utilization", 70.0)),
                        maintenance_status=str(r.get("maintenance_status", "Operational"))
                    ))
            elif entity_type == "equipment":
                existing = db.query(Equipment).filter(Equipment.equipment_id == str(r["equipment_id"])).first()
                if existing:
                    existing.quantity = int(r["quantity"])
                else:
                    db.add(Equipment(
                        equipment_id=str(r["equipment_id"]).strip(),
                        name=str(r["name"]).strip(),
                        equipment_type=str(r["equipment_type"]).strip(),
                        department_code=str(r["department_code"]).strip().upper(),
                        quantity=int(r["quantity"]),
                        operational_count=int(r.get("operational_count", r["quantity"])),
                        maintenance_count=int(r.get("maintenance_count", 0)),
                        status=str(r.get("status", "Operational"))
                    ))
        db.commit()

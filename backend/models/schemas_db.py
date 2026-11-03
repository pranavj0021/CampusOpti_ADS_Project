import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="student")  # "admin", "student", "faculty"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("PredictionRecord", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name or self.username,
            "role": self.role or "student",
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    roll_number = Column(String(50), nullable=True)
    department_code = Column(String(10), default="CS")
    cgpa = Column(Float, default=7.8)
    backlogs = Column(Integer, default=0)
    internships_count = Column(Integer, default=1)
    projects_count = Column(Integer, default=2)
    certifications_count = Column(Integer, default=1)
    coding_score = Column(Float, default=78.0)  # 0 to 100
    communication_score = Column(Float, default=82.0)  # 0 to 100
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="student_profile")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "roll_number": self.roll_number or "N/A",
            "department_code": self.department_code or "CS",
            "cgpa": float(self.cgpa) if self.cgpa is not None else 7.5,
            "backlogs": int(self.backlogs) if self.backlogs is not None else 0,
            "internships_count": int(self.internships_count) if self.internships_count is not None else 0,
            "projects_count": int(self.projects_count) if self.projects_count is not None else 0,
            "certifications_count": int(self.certifications_count) if self.certifications_count is not None else 0,
            "coding_score": float(self.coding_score) if self.coding_score is not None else 70.0,
            "communication_score": float(self.communication_score) if self.communication_score is not None else 75.0,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_name = Column(String(100), nullable=True)
    roll_number = Column(String(50), nullable=True)
    department_code = Column(String(10), nullable=False)
    cgpa = Column(Float, nullable=False)
    backlogs = Column(Integer, nullable=False)
    internships = Column(Integer, nullable=False)
    projects = Column(Integer, nullable=False)
    coding_score = Column(Float, nullable=False)
    communication_score = Column(Float, nullable=False)
    predicted_status = Column(String(50), nullable=False)  # "High Chance", "Moderate Chance", "Needs Improvement"
    placement_probability = Column(Float, nullable=False)  # 0.0 - 1.0
    risk_level = Column(String(20), default="Low")  # "Low", "Moderate", "High"
    model_used = Column(String(50), default="XGBoost")
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="predictions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "student_name": self.student_name,
            "roll_number": self.roll_number,
            "department_code": self.department_code,
            "cgpa": self.cgpa,
            "backlogs": self.backlogs,
            "internships": self.internships,
            "projects": self.projects,
            "coding_score": self.coding_score,
            "communication_score": self.communication_score,
            "predicted_status": self.predicted_status,
            "placement_probability": round(float(self.placement_probability), 4),
            "risk_level": self.risk_level,
            "model_used": self.model_used,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    building = Column(String(50), nullable=True)
    established_year = Column(Integer, default=2010)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "building": self.building,
            "established_year": self.established_year
        }

class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    department_code = Column(String(10), index=True, nullable=False)
    academic_year = Column(String(20), index=True, nullable=False)
    year_level = Column(Integer, default=1)
    semester = Column(String(10), default="Fall")
    program = Column(String(50), default="B.Tech")
    total_students = Column(Integer, nullable=False)
    divisions_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "department_code": self.department_code,
            "academic_year": self.academic_year,
            "year_level": self.year_level,
            "semester": self.semester,
            "program": self.program,
            "total_students": self.total_students,
            "divisions_count": self.divisions_count
        }

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(20), unique=True, index=True, nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    capacity = Column(Integer, nullable=False, default=60)
    room_type = Column(String(50), default="Lecture Hall")
    current_utilization = Column(Float, default=75.0)
    is_available = Column(Boolean, default=True)
    building_block = Column(String(50), default="Block A")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "department_code": self.department_code,
            "capacity": self.capacity,
            "room_type": self.room_type,
            "current_utilization": self.current_utilization,
            "is_available": self.is_available,
            "building_block": self.building_block
        }

class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    designation = Column(String(50), default="Assistant Professor")
    specialization = Column(String(100), default="Engineering")
    current_teaching_hours = Column(Float, default=14.0)
    max_workload_hours = Column(Float, default=16.0)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "faculty_id": self.faculty_id,
            "name": self.name,
            "department_code": self.department_code,
            "designation": self.designation,
            "specialization": self.specialization,
            "current_teaching_hours": self.current_teaching_hours,
            "max_workload_hours": self.max_workload_hours,
            "is_available": self.is_available
        }

class Laboratory(Base):
    __tablename__ = "laboratories"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(String(20), unique=True, index=True, nullable=False)
    lab_name = Column(String(100), nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    capacity = Column(Integer, nullable=False, default=30)
    computers_count = Column(Integer, default=30)
    current_utilization = Column(Float, default=70.0)
    is_available = Column(Boolean, default=True)
    maintenance_status = Column(String(50), default="Operational")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lab_id": self.lab_id,
            "lab_name": self.lab_name,
            "department_code": self.department_code,
            "capacity": self.capacity,
            "computers_count": self.computers_count,
            "current_utilization": self.current_utilization,
            "is_available": self.is_available,
            "maintenance_status": self.maintenance_status
        }

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(30), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    equipment_type = Column(String(50), nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    quantity = Column(Integer, nullable=False, default=10)
    operational_count = Column(Integer, default=9)
    maintenance_count = Column(Integer, default=1)
    status = Column(String(50), default="Operational")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "equipment_id": self.equipment_id,
            "name": self.name,
            "equipment_type": self.equipment_type,
            "department_code": self.department_code,
            "quantity": self.quantity,
            "operational_count": self.operational_count,
            "maintenance_count": self.maintenance_count,
            "status": self.status
        }

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(20), unique=True, index=True, nullable=False)
    course_name = Column(String(150), nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    subject_type = Column(String(50), default="Core")
    lecture_hours = Column(Integer, default=3)
    lab_hours = Column(Integer, default=2)
    weekly_hours = Column(Integer, default=5)
    credits = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AcademicCalendar(Base):
    __tablename__ = "academic_calendar"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String(20), index=True, nullable=False)
    semester = Column(String(20), nullable=False)
    instructional_weeks = Column(Integer, default=16)
    holidays_count = Column(Integer, default=12)
    admission_quota = Column(Integer, default=600)
    events_summary = Column(String(255), default="Orientation, Midterms, Final Exam")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DatasetImport(Base):
    __tablename__ = "dataset_imports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    total_rows = Column(Integer, default=0)
    accepted_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    validation_report = Column(JSON, nullable=True)
    status = Column(String(50), default="Success")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String(20), nullable=False)
    model_name = Column(String(50), nullable=False)
    resource_category = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=True)
    predictions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ResourceGapAnalysis(Base):
    __tablename__ = "resource_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String(20), index=True, nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    resource_category = Column(String(50), nullable=False)
    required_quantity = Column(Float, nullable=False)
    available_quantity = Column(Float, nullable=False)
    gap_quantity = Column(Float, nullable=False)
    utilization_rate = Column(Float, default=0.0)
    priority_score = Column(Float, default=0.0)
    recommendation_text = Column(Text, nullable=True)
    status = Column(String(20), default="Shortage")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AIExplanation(Base):
    __tablename__ = "ai_explanations"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_type = Column(String(50), default="general")
    model_used = Column(String(50), default="gpt-4o-mini")
    is_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

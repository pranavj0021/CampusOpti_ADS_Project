import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="admin")  # "admin", "planner", "viewer"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)  # CS, EC, ME, EE, CE
    name = Column(String(100), nullable=False)
    building = Column(String(50), nullable=True)
    established_year = Column(Integer, default=2010)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    department_code = Column(String(10), index=True, nullable=False)
    academic_year = Column(String(20), index=True, nullable=False)  # e.g., "2023-2024"
    year_level = Column(Integer, default=1)  # 1 to 4
    semester = Column(String(10), default="Fall")  # "Fall", "Spring"
    program = Column(String(50), default="B.Tech")
    total_students = Column(Integer, nullable=False)
    divisions_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(20), unique=True, index=True, nullable=False)
    course_name = Column(String(150), nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    subject_type = Column(String(50), default="Core")  # Core, Elective, Lab
    lecture_hours = Column(Integer, default=3)
    lab_hours = Column(Integer, default=2)
    weekly_hours = Column(Integer, default=5)
    credits = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(20), unique=True, index=True, nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    capacity = Column(Integer, nullable=False, default=60)
    room_type = Column(String(50), default="Lecture Hall")  # Lecture Hall, Smart Room, Seminar Hall
    current_utilization = Column(Float, default=75.0)  # Percentage 0-100
    is_available = Column(Boolean, default=True)
    building_block = Column(String(50), default="Block A")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    maintenance_status = Column(String(50), default="Operational")  # Operational, Needs Maintenance, Under Renovation
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(30), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    equipment_type = Column(String(50), nullable=False)  # Computer, Server, Oscilloscope, Projector, GPU Rig
    department_code = Column(String(10), index=True, nullable=False)
    quantity = Column(Integer, nullable=False, default=10)
    operational_count = Column(Integer, default=9)
    maintenance_count = Column(Integer, default=1)
    status = Column(String(50), default="Operational")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AcademicCalendar(Base):
    __tablename__ = "academic_calendar"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String(20), index=True, nullable=False)
    semester = Column(String(20), nullable=False)  # Fall / Spring
    instructional_weeks = Column(Integer, default=16)
    holidays_count = Column(Integer, default=12)
    admission_quota = Column(Integer, default=600)
    events_summary = Column(String(255), default="Orientation, Midterms, Final Exam, Tech Symposium")
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
    status = Column(String(50), default="Success")  # Success, Failed, Partial
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String(20), nullable=False)
    model_name = Column(String(50), nullable=False)
    resource_category = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=True)  # MAE, RMSE, R2
    predictions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ResourceGapAnalysis(Base):
    __tablename__ = "resource_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String(20), index=True, nullable=False)
    department_code = Column(String(10), index=True, nullable=False)
    resource_category = Column(String(50), nullable=False)  # Classrooms, Faculty, Laboratories, Equipment
    required_quantity = Column(Float, nullable=False)
    available_quantity = Column(Float, nullable=False)
    gap_quantity = Column(Float, nullable=False)  # Required - Available (>0 is Shortage, <0 is Surplus)
    utilization_rate = Column(Float, default=0.0)
    priority_score = Column(Float, default=0.0)  # 0 to 100
    recommendation_text = Column(Text, nullable=True)
    status = Column(String(20), default="Shortage")  # Shortage, Surplus, Balanced
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

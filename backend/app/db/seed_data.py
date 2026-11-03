import csv
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal, Base
from app.models.schemas_db import (
    User, Department, StudentEnrollment, Course, Classroom, 
    Faculty, Laboratory, Equipment, AcademicCalendar
)
from app.core.security import get_password_hash
from app.core.config import settings

def init_db(db: Session = None):
    Base.metadata.create_all(bind=engine)
    
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        # Check if already seeded
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                email="admin@campuspredict.edu",
                hashed_password=get_password_hash("admin123"),
                full_name="Dr. Sarah Jenkins (Dean of Academic Planning)",
                role="admin",
                is_active=True
            )
            db.add(admin_user)

        # Seed Departments if not present
        if db.query(Department).count() == 0:
            departments = [
                Department(code="CS", name="Computer Science & Engineering", building="Turing Block", established_year=2010),
                Department(code="AI", name="Artificial Intelligence & Data Science", building="Neumann Hall", established_year=2020),
                Department(code="EC", name="Electronics & Communication Engineering", building="Tesla Block", established_year=2010),
                Department(code="ME", name="Mechanical Engineering", building="Watt Pavilion", established_year=2008),
                Department(code="EE", name="Electrical & Electronics Engineering", building="Faraday Block", established_year=2009),
                Department(code="CE", name="Civil Engineering", building="Smeaton Hall", established_year=2008)
            ]
            db.add_all(departments)
            db.commit()

        # Seed Multi-Year Historical Student Enrollments (2019-2020 through 2025-2026)
        if db.query(StudentEnrollment).count() == 0:
            # Realistic growth patterns
            history = [
                # 2019-2020
                ("CS", "2019-2020", 1, 180, 3), ("CS", "2019-2020", 2, 175, 3), ("CS", "2019-2020", 3, 160, 3), ("CS", "2019-2020", 4, 155, 3),
                ("AI", "2019-2020", 1, 60, 1),
                ("EC", "2019-2020", 1, 120, 2), ("EC", "2019-2020", 2, 115, 2), ("EC", "2019-2020", 3, 110, 2), ("EC", "2019-2020", 4, 105, 2),
                ("ME", "2019-2020", 1, 120, 2), ("ME", "2019-2020", 2, 120, 2), ("ME", "2019-2020", 3, 115, 2), ("ME", "2019-2020", 4, 110, 2),
                ("EE", "2019-2020", 1, 90, 2),  ("EE", "2019-2020", 2, 85, 2),  ("EE", "2019-2020", 3, 80, 2),  ("EE", "2019-2020", 4, 80, 2),
                ("CE", "2019-2020", 1, 80, 2),  ("CE", "2019-2020", 2, 75, 2),  ("CE", "2019-2020", 3, 75, 2),  ("CE", "2019-2020", 4, 70, 2),
                
                # 2020-2021
                ("CS", "2020-2021", 1, 210, 4), ("CS", "2020-2021", 2, 178, 3), ("CS", "2020-2021", 3, 172, 3), ("CS", "2020-2021", 4, 158, 3),
                ("AI", "2020-2021", 1, 90, 2),  ("AI", "2020-2021", 2, 58, 1),
                ("EC", "2020-2021", 1, 125, 2), ("EC", "2020-2021", 2, 118, 2), ("EC", "2020-2021", 3, 114, 2), ("EC", "2020-2021", 4, 108, 2),
                ("ME", "2020-2021", 1, 115, 2), ("ME", "2020-2021", 2, 118, 2), ("ME", "2020-2021", 3, 117, 2), ("ME", "2020-2021", 4, 112, 2),
                ("EE", "2020-2021", 1, 95, 2),  ("EE", "2020-2021", 2, 88, 2),  ("EE", "2020-2021", 3, 84, 2),  ("EE", "2020-2021", 4, 78, 2),
                ("CE", "2020-2021", 1, 75, 2),  ("CE", "2020-2021", 2, 78, 2),  ("CE", "2020-2021", 3, 74, 2),  ("CE", "2020-2021", 4, 72, 2),

                # 2021-2022
                ("CS", "2021-2022", 1, 240, 4), ("CS", "2021-2022", 2, 205, 4), ("CS", "2021-2022", 3, 175, 3), ("CS", "2021-2022", 4, 170, 3),
                ("AI", "2021-2022", 1, 120, 2), ("AI", "2021-2022", 2, 88, 2),  ("AI", "2021-2022", 3, 56, 1),
                ("EC", "2021-2022", 1, 130, 2), ("EC", "2021-2022", 2, 122, 2), ("EC", "2021-2022", 3, 116, 2), ("EC", "2021-2022", 4, 112, 2),
                ("ME", "2021-2022", 1, 110, 2), ("ME", "2021-2022", 2, 112, 2), ("ME", "2021-2022", 3, 115, 2), ("ME", "2021-2022", 4, 115, 2),
                ("EE", "2021-2022", 1, 95, 2),  ("EE", "2021-2022", 2, 92, 2),  ("EE", "2021-2022", 3, 86, 2),  ("EE", "2021-2022", 4, 82, 2),
                ("CE", "2021-2022", 1, 70, 2),  ("CE", "2021-2022", 2, 73, 2),  ("CE", "2021-2022", 3, 76, 2),  ("CE", "2021-2022", 4, 72, 2),

                # 2022-2023
                ("CS", "2022-2023", 1, 270, 5), ("CS", "2022-2023", 2, 235, 4), ("CS", "2022-2023", 3, 202, 4), ("CS", "2022-2023", 4, 173, 3),
                ("AI", "2022-2023", 1, 150, 3), ("AI", "2022-2023", 2, 116, 2), ("AI", "2022-2023", 3, 85, 2),  ("AI", "2022-2023", 4, 55, 1),
                ("EC", "2022-2023", 1, 135, 2), ("EC", "2022-2023", 2, 128, 2), ("EC", "2022-2023", 3, 120, 2), ("EC", "2022-2023", 4, 114, 2),
                ("ME", "2022-2023", 1, 105, 2), ("ME", "2022-2023", 2, 108, 2), ("ME", "2022-2023", 3, 110, 2), ("ME", "2022-2023", 4, 112, 2),
                ("EE", "2022-2023", 1, 100, 2), ("EE", "2022-2023", 2, 94, 2),  ("EE", "2022-2023", 3, 90, 2),  ("EE", "2022-2023", 4, 85, 2),
                ("CE", "2022-2023", 1, 68, 2),  ("CE", "2022-2023", 2, 69, 2),  ("CE", "2022-2023", 3, 71, 2),  ("CE", "2022-2023", 4, 74, 2),

                # 2023-2024
                ("CS", "2023-2024", 1, 300, 5), ("CS", "2023-2024", 2, 265, 5), ("CS", "2023-2024", 3, 230, 4), ("CS", "2023-2024", 4, 198, 4),
                ("AI", "2023-2024", 1, 180, 3), ("AI", "2023-2024", 2, 146, 3), ("AI", "2023-2024", 3, 112, 2), ("AI", "2023-2024", 4, 82, 2),
                ("EC", "2023-2024", 1, 140, 3), ("EC", "2023-2024", 2, 132, 2), ("EC", "2023-2024", 3, 126, 2), ("EC", "2023-2024", 4, 118, 2),
                ("ME", "2023-2024", 1, 100, 2), ("ME", "2023-2024", 2, 103, 2), ("ME", "2023-2024", 3, 106, 2), ("ME", "2023-2024", 4, 108, 2),
                ("EE", "2023-2024", 1, 102, 2), ("EE", "2023-2024", 2, 98, 2),  ("EE", "2023-2024", 3, 92, 2),  ("EE", "2023-2024", 4, 88, 2),
                ("CE", "2023-2024", 1, 65, 2),  ("CE", "2023-2024", 2, 66, 2),  ("CE", "2023-2024", 3, 67, 2),  ("CE", "2023-2024", 4, 70, 2),

                # 2024-2025
                ("CS", "2024-2025", 1, 330, 6), ("CS", "2024-2025", 2, 295, 5), ("CS", "2024-2025", 3, 260, 5), ("CS", "2024-2025", 4, 226, 4),
                ("AI", "2024-2025", 1, 210, 4), ("AI", "2024-2025", 2, 175, 3), ("AI", "2024-2025", 3, 142, 3), ("AI", "2024-2025", 4, 108, 2),
                ("EC", "2024-2025", 1, 145, 3), ("EC", "2024-2025", 2, 138, 3), ("EC", "2024-2025", 3, 130, 2), ("EC", "2024-2025", 4, 122, 2),
                ("ME", "2024-2025", 1, 95, 2),  ("ME", "2024-2025", 2, 98, 2),  ("ME", "2024-2025", 3, 101, 2), ("ME", "2024-2025", 4, 104, 2),
                ("EE", "2024-2025", 1, 105, 2), ("EE", "2024-2025", 2, 100, 2), ("EE", "2024-2025", 3, 95, 2),  ("EE", "2024-2025", 4, 90, 2),
                ("CE", "2024-2025", 1, 62, 1),  ("CE", "2024-2025", 2, 63, 1),  ("CE", "2024-2025", 3, 64, 1),  ("CE", "2024-2025", 4, 66, 1),

                # 2025-2026 (Current Academic Year)
                ("CS", "2025-2026", 1, 360, 6), ("CS", "2025-2026", 2, 325, 6), ("CS", "2025-2026", 3, 290, 5), ("CS", "2025-2026", 4, 255, 5),
                ("AI", "2025-2026", 1, 240, 4), ("AI", "2025-2026", 2, 205, 4), ("AI", "2025-2026", 3, 170, 3), ("AI", "2025-2026", 4, 138, 3),
                ("EC", "2025-2026", 1, 150, 3), ("EC", "2025-2026", 2, 142, 3), ("EC", "2025-2026", 3, 135, 2), ("EC", "2025-2026", 4, 128, 2),
                ("ME", "2025-2026", 1, 92, 2),  ("ME", "2025-2026", 2, 94, 2),  ("ME", "2025-2026", 3, 96, 2),  ("ME", "2025-2026", 4, 100, 2),
                ("EE", "2025-2026", 1, 108, 2), ("EE", "2025-2026", 2, 102, 2), ("EE", "2025-2026", 3, 98, 2),  ("EE", "2025-2026", 4, 93, 2),
                ("CE", "2025-2026", 1, 60, 1),  ("CE", "2025-2026", 2, 61, 1),  ("CE", "2025-2026", 3, 62, 1),  ("CE", "2025-2026", 4, 63, 1),
            ]

            enrollment_objects = []
            for dept, yr, lvl, count, divs in history:
                enrollment_objects.append(StudentEnrollment(
                    department_code=dept,
                    academic_year=yr,
                    year_level=lvl,
                    semester="Fall",
                    program="B.Tech",
                    total_students=count,
                    divisions_count=divs
                ))
            db.add_all(enrollment_objects)
            db.commit()

        # Seed Classrooms (36 classrooms)
        if db.query(Classroom).count() == 0:
            classrooms = []
            # CS (8 rooms)
            for i in range(1, 9):
                classrooms.append(Classroom(
                    room_id=f"CS-{100+i}", department_code="CS", capacity=65 if i <= 6 else 120,
                    room_type="Smart Classroom" if i % 2 == 0 else "Lecture Hall",
                    current_utilization=88.5 if i <= 4 else 82.0, is_available=True, building_block="Turing Block"
                ))
            # AI (4 rooms)
            for i in range(1, 5):
                classrooms.append(Classroom(
                    room_id=f"AI-{200+i}", department_code="AI", capacity=65 if i <= 3 else 100,
                    room_type="Smart Classroom",
                    current_utilization=92.0, is_available=True, building_block="Neumann Hall"
                ))
            # EC (6 rooms)
            for i in range(1, 7):
                classrooms.append(Classroom(
                    room_id=f"EC-{300+i}", department_code="EC", capacity=60,
                    room_type="Lecture Hall" if i <= 4 else "Seminar Room",
                    current_utilization=74.0, is_available=True, building_block="Tesla Block"
                ))
            # ME (6 rooms)
            for i in range(1, 7):
                classrooms.append(Classroom(
                    room_id=f"ME-{400+i}", department_code="ME", capacity=60,
                    room_type="Lecture Hall",
                    current_utilization=61.0, is_available=True, building_block="Watt Pavilion"
                ))
            # EE (5 rooms)
            for i in range(1, 6):
                classrooms.append(Classroom(
                    room_id=f"EE-{500+i}", department_code="EE", capacity=60,
                    room_type="Lecture Hall",
                    current_utilization=68.0, is_available=True, building_block="Faraday Block"
                ))
            # CE (5 rooms)
            for i in range(1, 6):
                classrooms.append(Classroom(
                    room_id=f"CE-{600+i}", department_code="CE", capacity=55,
                    room_type="Lecture Hall",
                    current_utilization=52.0, is_available=True, building_block="Smeaton Hall"
                ))
            db.add_all(classrooms)
            db.commit()

        # Seed Faculty (48 faculty members)
        if db.query(Faculty).count() == 0:
            faculty_members = []
            faculty_specs = [
                ("CS", 14, "Prof. & Ass. Prof. in Computing", 15.5),
                ("AI", 7,  "Ass. Prof. & Researchers in ML/Data", 16.0),
                ("EC", 9,  "Communication, Signal Processing, VLSI", 13.8),
                ("ME", 7,  "Thermal, Robotics, Manufacturing", 12.0),
                ("EE", 6,  "Power Systems, Control Systems", 13.0),
                ("CE", 5,  "Structures, Geotechnical, Surveying", 11.5),
            ]
            
            f_id = 101
            for dept, count, spec, workload in faculty_specs:
                for idx in range(1, count + 1):
                    role = "Professor" if idx == 1 else ("Associate Professor" if idx <= 3 else "Assistant Professor")
                    faculty_members.append(Faculty(
                        faculty_id=f"FAC-{dept}-{f_id}",
                        name=f"Dr. {dept} Faculty {idx}",
                        department_code=dept,
                        designation=role,
                        specialization=spec,
                        current_teaching_hours=workload,
                        max_workload_hours=16.0,
                        is_available=True
                    ))
                    f_id += 1
            db.add_all(faculty_members)
            db.commit()

        # Seed Laboratories (18 laboratories)
        if db.query(Laboratory).count() == 0:
            labs = [
                Laboratory(lab_id="LAB-CS-1", lab_name="Software Engineering Lab", department_code="CS", capacity=35, computers_count=35, current_utilization=90.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-CS-2", lab_name="Advanced Cloud Computing Lab", department_code="CS", capacity=35, computers_count=35, current_utilization=88.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-CS-3", lab_name="Cybersecurity & Networks Lab", department_code="CS", capacity=30, computers_count=30, current_utilization=85.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-AI-1", lab_name="Deep Learning & GPU Supercomputing Lab", department_code="AI", capacity=35, computers_count=35, current_utilization=95.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-AI-2", lab_name="Data Analytics & Vision Lab", department_code="AI", capacity=30, computers_count=30, current_utilization=92.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-EC-1", lab_name="VLSI Design & Embedded Systems Lab", department_code="EC", capacity=30, computers_count=30, current_utilization=78.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-EC-2", lab_name="Microwave & DSP Communications Lab", department_code="EC", capacity=25, computers_count=20, current_utilization=72.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-EC-3", lab_name="IoT & Hardware Prototyping Lab", department_code="EC", capacity=30, computers_count=25, current_utilization=80.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-ME-1", lab_name="CAD/CAM & Simulation Lab", department_code="ME", capacity=30, computers_count=30, current_utilization=65.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-ME-2", lab_name="Thermal Systems & IC Engines Lab", department_code="ME", capacity=25, computers_count=5, current_utilization=58.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-ME-3", lab_name="Robotics & Mechatronics Lab", department_code="ME", capacity=25, computers_count=15, current_utilization=64.0, maintenance_status="Needs Maintenance"),
                Laboratory(lab_id="LAB-EE-1", lab_name="Power Electronics & Drives Lab", department_code="EE", capacity=25, computers_count=15, current_utilization=70.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-EE-2", lab_name="Electrical Machines & Smart Grid Lab", department_code="EE", capacity=25, computers_count=10, current_utilization=66.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-EE-3", lab_name="Renewable Energy Simulation Lab", department_code="EE", capacity=25, computers_count=25, current_utilization=72.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-CE-1", lab_name="Structural Mechanics & Concrete Lab", department_code="CE", capacity=25, computers_count=5, current_utilization=50.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-CE-2", lab_name="Geotechnical & Soil Testing Lab", department_code="CE", capacity=20, computers_count=5, current_utilization=48.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-CE-3", lab_name="GIS, Remote Sensing & Surveying Lab", department_code="CE", capacity=25, computers_count=25, current_utilization=55.0, maintenance_status="Operational"),
                Laboratory(lab_id="LAB-CE-4", lab_name="Environmental Engineering Lab", department_code="CE", capacity=20, computers_count=5, current_utilization=45.0, maintenance_status="Operational"),
            ]
            db.add_all(labs)
            db.commit()

        # Seed Equipment
        if db.query(Equipment).count() == 0:
            equipments = [
                Equipment(equipment_id="EQ-CS-01", name="High-Performance Dell Precision Workstations", equipment_type="Computer", department_code="CS", quantity=110, operational_count=104, maintenance_count=6, status="Operational"),
                Equipment(equipment_id="EQ-CS-02", name="Rackmounted Edge Server Nodes", equipment_type="Server", department_code="CS", quantity=8, operational_count=7, maintenance_count=1, status="Operational"),
                Equipment(equipment_id="EQ-AI-01", name="NVIDIA A100 / RTX 4090 Deep Learning Stations", equipment_type="GPU Rig", department_code="AI", quantity=65, operational_count=60, maintenance_count=5, status="Operational"),
                Equipment(equipment_id="EQ-AI-02", name="High-Throughput SAN Storage Array", equipment_type="Server", department_code="AI", quantity=4, operational_count=4, maintenance_count=0, status="Operational"),
                Equipment(equipment_id="EQ-EC-01", name="Digital Storage Mixed-Signal Oscilloscopes", equipment_type="Oscilloscope", department_code="EC", quantity=35, operational_count=31, maintenance_count=4, status="Operational"),
                Equipment(equipment_id="EQ-EC-02", name="FPGA Development Boards (Xilinx)", equipment_type="Hardware Rig", department_code="EC", quantity=45, operational_count=42, maintenance_count=3, status="Operational"),
                Equipment(equipment_id="EQ-ME-01", name="Industrial 3D Printing & Prototyping Systems", equipment_type="3D Printer", department_code="ME", quantity=10, operational_count=8, maintenance_count=2, status="Operational"),
                Equipment(equipment_id="EQ-ME-02", name="Universal Testing Machine (UTM)", equipment_type="Testing Rig", department_code="ME", quantity=3, operational_count=2, maintenance_count=1, status="Needs Calibration"),
                Equipment(equipment_id="EQ-EE-01", name="Digital Power Quality Analyzers", equipment_type="Testing Rig", department_code="EE", quantity=15, operational_count=13, maintenance_count=2, status="Operational"),
                Equipment(equipment_id="EQ-EE-02", name="Programmable DC Power Supplies & Loads", equipment_type="Power Unit", department_code="EE", quantity=25, operational_count=23, maintenance_count=2, status="Operational"),
                Equipment(equipment_id="EQ-CE-01", name="Digital Total Station & Theodolites", equipment_type="Surveying Rig", department_code="CE", quantity=12, operational_count=11, maintenance_count=1, status="Operational"),
                Equipment(equipment_id="EQ-CE-02", name="Triaxial Soil Shear Apparatus", equipment_type="Testing Rig", department_code="CE", quantity=4, operational_count=4, maintenance_count=0, status="Operational"),
            ]
            db.add_all(equipments)
            db.commit()

        # Seed Academic Calendar
        if db.query(AcademicCalendar).count() == 0:
            cal = [
                AcademicCalendar(academic_year="2024-2025", semester="Fall", instructional_weeks=16, holidays_count=12, admission_quota=950),
                AcademicCalendar(academic_year="2024-2025", semester="Spring", instructional_weeks=16, holidays_count=10, admission_quota=950),
                AcademicCalendar(academic_year="2025-2026", semester="Fall", instructional_weeks=16, holidays_count=12, admission_quota=1050),
                AcademicCalendar(academic_year="2025-2026", semester="Spring", instructional_weeks=16, holidays_count=10, admission_quota=1050),
                AcademicCalendar(academic_year="2026-2027", semester="Fall", instructional_weeks=16, holidays_count=12, admission_quota=1180),
            ]
            db.add_all(cal)
            db.commit()

        # Seed Courses
        if db.query(Course).count() == 0:
            courses = [
                Course(course_id="CS101", course_name="Data Structures & Algorithms", department_code="CS", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="CS201", course_name="Database Management Systems", department_code="CS", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="CS301", course_name="Cloud Computing & Distributed Systems", department_code="CS", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="AI101", course_name="Foundations of Machine Learning", department_code="AI", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="AI201", course_name="Deep Learning & Neural Networks", department_code="AI", subject_type="Core", lecture_hours=3, lab_hours=3, weekly_hours=6, credits=4),
                Course(course_id="EC101", course_name="Signals and Systems", department_code="EC", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="EC201", course_name="VLSI Design Methodologies", department_code="EC", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="ME101", course_name="Thermodynamics & Heat Transfer", department_code="ME", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="ME201", course_name="Computer-Aided Design and Manufacturing", department_code="ME", subject_type="Core", lecture_hours=3, lab_hours=3, weekly_hours=6, credits=4),
                Course(course_id="EE101", course_name="Power Electronics & Microgrids", department_code="EE", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
                Course(course_id="CE101", course_name="Structural Analysis & Steel Design", department_code="CE", subject_type="Core", lecture_hours=3, lab_hours=2, weekly_hours=5, credits=4),
            ]
            db.add_all(courses)
            db.commit()

        # Export sample CSV files and Excel template into data/sample and data/templates
        export_sample_files(db)

    finally:
        if should_close:
            db.close()

def export_sample_files(db: Session):
    sample_dir = settings.DATA_DIR / "sample"
    templates_dir = settings.DATA_DIR / "templates"
    sample_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Export students.csv
    students = db.query(StudentEnrollment).all()
    if students:
        df_students = pd.DataFrame([{
            "department_code": s.department_code,
            "academic_year": s.academic_year,
            "year_level": s.year_level,
            "semester": s.semester,
            "program": s.program,
            "total_students": s.total_students,
            "divisions_count": s.divisions_count
        } for s in students])
        df_students.to_csv(sample_dir / "students.csv", index=False)

    # Export classrooms.csv
    rooms = db.query(Classroom).all()
    if rooms:
        df_rooms = pd.DataFrame([{
            "room_id": r.room_id,
            "department_code": r.department_code,
            "capacity": r.capacity,
            "room_type": r.room_type,
            "current_utilization": r.current_utilization,
            "is_available": r.is_available,
            "building_block": r.building_block
        } for r in rooms])
        df_rooms.to_csv(sample_dir / "classrooms.csv", index=False)

    # Export faculty.csv
    faculty = db.query(Faculty).all()
    if faculty:
        df_faculty = pd.DataFrame([{
            "faculty_id": f.faculty_id,
            "name": f.name,
            "department_code": f.department_code,
            "designation": f.designation,
            "specialization": f.specialization,
            "current_teaching_hours": f.current_teaching_hours,
            "max_workload_hours": f.max_workload_hours,
            "is_available": f.is_available
        } for f in faculty])
        df_faculty.to_csv(sample_dir / "faculty.csv", index=False)

    # Export laboratories.csv
    labs = db.query(Laboratory).all()
    if labs:
        df_labs = pd.DataFrame([{
            "lab_id": l.lab_id,
            "lab_name": l.lab_name,
            "department_code": l.department_code,
            "capacity": l.capacity,
            "computers_count": l.computers_count,
            "current_utilization": l.current_utilization,
            "maintenance_status": l.maintenance_status
        } for l in labs])
        df_labs.to_csv(sample_dir / "laboratories.csv", index=False)

    # Export equipment.csv
    equipment = db.query(Equipment).all()
    if equipment:
        df_equipment = pd.DataFrame([{
            "equipment_id": e.equipment_id,
            "name": e.name,
            "equipment_type": e.equipment_type,
            "department_code": e.department_code,
            "quantity": e.quantity,
            "operational_count": e.operational_count,
            "maintenance_count": e.maintenance_count,
            "status": e.status
        } for e in equipment])
        df_equipment.to_csv(sample_dir / "equipment.csv", index=False)

    # Create multi-sheet Excel Template
    with pd.ExcelWriter(templates_dir / "campus_resource_template.xlsx", engine="openpyxl") as writer:
        if students:
            df_students.head(10).to_excel(writer, sheet_name="Students", index=False)
        if rooms:
            df_rooms.head(10).to_excel(writer, sheet_name="Classrooms", index=False)
        if faculty:
            df_faculty.head(10).to_excel(writer, sheet_name="Faculty", index=False)
        if labs:
            df_labs.head(10).to_excel(writer, sheet_name="Laboratories", index=False)
        if equipment:
            df_equipment.head(10).to_excel(writer, sheet_name="Equipment", index=False)

if __name__ == "__main__":
    init_db()
    print("Database successfully initialized and seeded with academic records!")

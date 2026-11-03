# CampusPredict — Streamlit + Flask + Docker Architecture

**CampusPredict** is an end-to-end AI-powered web platform designed for colleges and universities to forecast student placement probability, track student academic performance, and forecast institutional campus resource demands.

---

## Architecture Overview

- **Frontend:** Python [Streamlit](https://streamlit.io/) (Port `8501`) with multi-page structure:
  - `streamlit_app.py` — Authentication portal (Login & Registration)
  - `pages/1_Dashboard.py` — Real-time placement and institutional KPI dashboard
  - `pages/2_Student_Profile.py` — Academic details, CGPA, backlogs, skills tracking
  - `pages/3_Placement_Prediction.py` — Multi-model placement forecasting (XGBoost, Random Forest, Logistic Regression)
  - `pages/4_Prediction_History.py` — Database audit history of past predictions
  - `pages/5_Analytics.py` — Cross-department benchmarks and correlations
  - `pages/6_AI_Chatbot.py` — Grounded AI placement advisor and career counseling
  - `pages/7_Settings_and_Logout.py` — System diagnostics and session controls
- **Backend API:** Python [Flask](https://flask.palletsprojects.com/) REST API (Port `5000`) with Waitress WSGI
- **Machine Learning Engine:** Scikit-Learn & XGBoost models (`saved_models/`)
- **Database:** SQLite (`backend/campuspredict.db`) with persistent volume mounts
- **Containerization:** Docker & Docker Compose

---

## Quickstart: Local Setup (Without Docker)

### 1. Prerequisites
- Python 3.10+ installed
- SQLite3

### 2. Backend Startup
In your first terminal:
```powershell
cd C:\ADSL\backend
python app.py
```
*The Flask REST API will start on `http://localhost:5000` using Waitress WSGI.*  
Verify health check: `http://localhost:5000/api/health`

### 3. Frontend Startup
In a second terminal:
```powershell
cd C:\ADSL
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```
*Access the web application at:* `http://localhost:8501`

---

## Quickstart: Docker Setup

To run both services with container networking and persistent database storage:

```powershell
cd C:\ADSL
docker compose up --build
```

### Deployed Services:
- **Streamlit Frontend:** `http://localhost:8501`
- **Flask REST API:** `http://localhost:5000`
- **Health Check Endpoint:** `http://localhost:5000/api/health`

---

## Default Access Credentials

- **Administrator:**
  - Username: `admin`
  - Password: `admin123`
- **New Registration:**
  - Switch to the "Create Account" tab on the login screen to register a new student or faculty account.

---

## Key API Endpoints

- `GET  /api/health` — Health check & database connection probe
- `POST /api/auth/register` — Create new student/faculty account
- `POST /api/auth/login` — Authenticate and receive JWT Bearer token
- `GET  /api/auth/me` — Authenticated user details
- `POST /api/auth/logout` — Invalidate user session
- `GET  /api/students/profile` — Fetch student profile & competencies
- `PUT  /api/students/profile` — Update student profile
- `POST /api/predictions` — Run placement ML prediction & persist result
- `GET  /api/predictions/history` — Fetch user's authorized prediction history
- `GET  /api/analytics` — Calculate live institutional analytics
- `GET  /api/dashboard/overview` — Fetch campus KPIs and department projections
- `GET  /api/ml/models` — List candidate ML models & evaluations

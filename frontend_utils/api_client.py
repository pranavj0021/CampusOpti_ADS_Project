import os
import requests
from typing import Dict, Any, Optional

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api").rstrip("/")

class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def check_health(self) -> Dict[str, Any]:
        """Checks backend health status."""
        try:
            res = requests.get(f"{self.base_url}/health", timeout=5)
            if res.status_code == 200:
                return res.json()
            return {"status": "error", "code": res.status_code}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    # ==========================
    # AUTHENTICATION
    # ==========================
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticates user against backend API."""
        try:
            res = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                headers=self._headers(),
                timeout=8
            )
            data = res.json()
            if res.status_code == 200:
                return {"success": True, "data": data}
            return {"success": False, "error": data.get("detail") or data.get("error", "Login failed")}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Cannot connect to Backend API at {self.base_url}. Ensure Flask is running."}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    def register(self, username: str, email: str, password: str, full_name: str = "", role: str = "student") -> Dict[str, Any]:
        """Registers a new user account."""
        try:
            res = requests.post(
                f"{self.base_url}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "role": role
                },
                headers=self._headers(),
                timeout=8
            )
            data = res.json()
            if res.status_code == 201:
                return {"success": True, "data": data}
            return {"success": False, "error": data.get("detail") or data.get("error", "Registration failed")}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Cannot connect to Backend API at {self.base_url}. Ensure Flask is running."}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    def get_me(self, token: str) -> Dict[str, Any]:
        """Fetches profile of currently authenticated user."""
        try:
            res = requests.get(f"{self.base_url}/auth/me", headers=self._headers(token), timeout=8)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Failed to get user")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================
    # STUDENT PROFILE
    # ==========================
    def get_student_profile(self, token: str) -> Dict[str, Any]:
        """Retrieves student profile."""
        try:
            res = requests.get(f"{self.base_url}/students/profile", headers=self._headers(token), timeout=8)
            if res.status_code == 200:
                return {"success": True, "data": res.json().get("profile", {})}
            return {"success": False, "error": res.json().get("detail", "Failed to get student profile")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_student_profile(self, token: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates student academic and skills profile."""
        try:
            res = requests.put(
                f"{self.base_url}/students/profile",
                json=profile_data,
                headers=self._headers(token),
                timeout=8
            )
            data = res.json()
            if res.status_code == 200:
                return {"success": True, "data": data.get("profile", {})}
            return {"success": False, "error": data.get("detail") or data.get("error", "Update failed")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================
    # PREDICTIONS
    # ==========================
    def create_prediction(self, token: str, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes placement prediction and saves to database."""
        try:
            res = requests.post(
                f"{self.base_url}/predictions",
                json=prediction_data,
                headers=self._headers(token),
                timeout=10
            )
            data = res.json()
            if res.status_code == 201:
                return {"success": True, "data": data.get("prediction", {})}
            return {"success": False, "error": data.get("detail") or data.get("error", "Prediction failed")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_prediction_history(self, token: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetches authorized prediction history records."""
        try:
            url = f"{self.base_url}/predictions/history"
            if user_id:
                url += f"?user_id={user_id}"
            res = requests.get(url, headers=self._headers(token), timeout=8)
            if res.status_code == 200:
                return {"success": True, "data": res.json().get("history", [])}
            return {"success": False, "error": res.json().get("detail", "Failed to fetch history")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================
    # ANALYTICS & DASHBOARD
    # ==========================
    def get_analytics(self, token: str) -> Dict[str, Any]:
        """Fetches calculated analytics from database."""
        try:
            res = requests.get(f"{self.base_url}/analytics", headers=self._headers(token), timeout=8)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Failed to fetch analytics")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_dashboard_overview(self, token: str, academic_year: str = "2026-2027") -> Dict[str, Any]:
        """Fetches dashboard KPIs and forecasts."""
        try:
            res = requests.get(
                f"{self.base_url}/dashboard/overview?academic_year={academic_year}",
                headers=self._headers(token),
                timeout=8
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.json().get("detail", "Failed to fetch dashboard")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_departments(self) -> Dict[str, Any]:
        """Fetches list of university departments."""
        try:
            res = requests.get(f"{self.base_url}/dashboard/departments", headers=self._headers(), timeout=5)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": "Failed to fetch departments"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_models_info(self) -> Dict[str, Any]:
        """Fetches candidate models and evaluations."""
        try:
            res = requests.get(f"{self.base_url}/ml/models", headers=self._headers(), timeout=5)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": "Failed to fetch models info"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================
    # GENERATIVE AI DECISION SUPPORT
    # ==========================
    def chat_ai(self, token: str, message: str, academic_year: str = "2026-2027") -> Dict[str, Any]:
        """Sends user query to CampusPredict AI decision assistant."""
        try:
            res = requests.post(
                f"{self.base_url}/ai/chat",
                json={"message": message, "academic_year": academic_year},
                headers=self._headers(token),
                timeout=15
            )
            data = res.json()
            if res.status_code == 200:
                return {"success": True, "data": data}
            return {"success": False, "error": data.get("detail") or data.get("error", "AI Advisor failed")}
        except Exception as e:
            return {"success": False, "error": str(e)}

api_client = ApiClient()

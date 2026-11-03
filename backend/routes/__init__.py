from routes.auth_routes import auth_bp
from routes.students_routes import students_bp
from routes.predictions_routes import predictions_bp
from routes.analytics_routes import analytics_bp
from routes.dashboard_routes import dashboard_bp
from routes.ml_routes import ml_bp
from routes.ai_routes import ai_bp

__all__ = [
    "auth_bp",
    "students_bp",
    "predictions_bp",
    "analytics_bp",
    "dashboard_bp",
    "ml_bp",
    "ai_bp"
]

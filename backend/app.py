import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import engine, Base, SessionLocal
from models import (
    User, StudentProfile, PredictionRecord, Department, StudentEnrollment,
    Classroom, Faculty, Laboratory, Equipment
)
from routes import (
    auth_bp, students_bp, predictions_bp, analytics_bp, dashboard_bp, ml_bp, ai_bp
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Safe DB table initialization (preserves existing data, creates new tables)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[Warning] DB table creation warning: {e}")

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(ai_bp)

    # Health Check endpoints
    @app.route("/health", methods=["GET"])
    @app.route("/api/health", methods=["GET"])
    def health_check():
        db_status = "connected"
        try:
            db = SessionLocal()
            db.execute(Base.metadata.tables["users"].select().limit(1))
            db.close()
        except Exception:
            db_status = "error"

        return jsonify({
            "status": "healthy",
            "service": "CampusPredict Flask Backend",
            "version": Config.VERSION,
            "database": db_status
        }), 200

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found", "detail": "The requested resource was not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method Not Allowed", "detail": "HTTP method not allowed for this endpoint"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal Server Error", "detail": "An unexpected error occurred on the server"}), 500

    return app

app = create_app()

if __name__ == "__main__":
    try:
        from waitress import serve
        print(f"Starting CampusPredict Flask Backend on http://{Config.HOST}:{Config.PORT} using Waitress WSGI...")
        serve(app, host=Config.HOST, port=Config.PORT)
    except ImportError:
        print(f"Starting CampusPredict Flask Backend on http://{Config.HOST}:{Config.PORT} using Flask dev server...")
        app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

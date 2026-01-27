from flask import Flask
from flask_cors import CORS
from database import get_db_connection
from flask_jwt_extended import JWTManager
from datetime import timedelta
from routes.auth_login import login_bp
from routes.logout import logout_bp
from routes.form import form_bp
from routes.user import user_bp
from routes.business_unit import business_unit_bp
from routes.compliance import compliance_bp
from routes.dashboard import dashboard_bp
from routes.activity_log import activity_log_bp
from routes.calender import calender_bp
from routes.form_submission import form_submission_bp
from routes.assessment import assessment_bp
from routes.user_department import user_department_bp
from routes.report import report_bp
from routes.settings import settings_bp
from routes.out_of_office import out_of_office_bp



app = Flask(__name__)

# 🔐 JWT CONFIG (CORRECT)
app.config["JWT_SECRET_KEY"] = "change_this_to_a_strong_secret"
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

jwt = JWTManager(app)

CORS(app, supports_credentials=True)

@app.route('/')
def home():
    return "Flask is running!"

@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        cursor.close()
        conn.close()
        return f"Connected to database: {db_name['DATABASE()']}"
    except Exception as e:
        return f"Error connecting to database: {e}"

# Blueprints
app.register_blueprint(form_bp, url_prefix="/form")
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(login_bp, url_prefix="/login")
app.register_blueprint(compliance_bp, url_prefix="/compliance")
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(user_department_bp)
app.register_blueprint(business_unit_bp)
app.register_blueprint(activity_log_bp)
app.register_blueprint(calender_bp)
app.register_blueprint(form_submission_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(report_bp)

app.register_blueprint(settings_bp)

app.register_blueprint(out_of_office_bp)

if __name__ == '__main__':
    app.run(port=5001, debug=True)


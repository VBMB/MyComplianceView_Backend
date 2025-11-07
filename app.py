from flask import Flask
from flask_cors import CORS
from database import get_db_connection


from routes.auth_login import login_bp
from routes.form import form_bp
from routes.user import user_bp
from routes.business_unit_add import business_unit_add_bp
from routes.business_unit_all import business_unit_all_bp
from routes.user_departments_add import user_departments_add_bp
from routes.user_departments_all import user_departments_all_bp
from routes.compliance import compliance_bp
from routes.dashboard import dashboard_bp
from routes.activity_log import activity_log_bp
from routes.user_update import user_update_bp
from routes.report import report_bp

app: Flask = Flask(__name__)

app.secret_key = "your_super_secret_key_here"

CORS(app, supports_credentials=True)

# CORS(app, origins=["http://localhost:3000"])

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




app.register_blueprint(form_bp, url_prefix="/form")
app.register_blueprint(user_bp, url_prefix="/user")


app.register_blueprint(login_bp, url_prefix="/login")

app.register_blueprint(compliance_bp, url_prefix="/compliance")

app.register_blueprint(dashboard_bp, url_prefix="/dashboard")


app.register_blueprint(business_unit_add_bp)

app.register_blueprint(business_unit_all_bp)

app.register_blueprint(user_departments_add_bp)

app.register_blueprint(user_departments_all_bp, url_prefix="/user/departments")

app.register_blueprint(activity_log_bp)

app.register_blueprint(user_update_bp)

app.register_blueprint(report_bp)







if __name__ == '__main__':
    app.run(debug=True)

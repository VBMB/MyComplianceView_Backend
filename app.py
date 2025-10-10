from flask import Flask


from database import get_db_connection
from routes.auth_login import login_bp
from routes.form import form_bp
from routes.user import user_bp
from routes.business_unit_add import business_unit_add_bp
from routes.business_unit_all import business_unit_all_bp
from routes.user_departments_add import user_departments_add_bp
from routes.user_departments_all import user_departments_all_bp


app: Flask = Flask(__name__)


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




app.register_blueprint(form_bp, url_prefix='/form')
app.register_blueprint(user_bp, url_prefix="/user")


app.register_blueprint(login_bp)

app.register_blueprint(business_unit_add_bp)

app.register_blueprint(business_unit_all_bp)

app.register_blueprint(user_departments_add_bp, url_prefix="/user/departments")

app.register_blueprint(user_departments_all_bp, url_prefix="/user/departments")








if __name__ == '__main__':
    app.run(debug=True)

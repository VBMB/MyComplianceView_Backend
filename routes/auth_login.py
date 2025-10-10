from flask import Blueprint, request, jsonify
from database import get_db_connection

login_bp = Blueprint('login_bp', __name__, url_prefix="/login")

@login_bp.route('/', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT usrlst_id, usrlst_name, usrlst_email, usrlst_role, usrlst_department
            FROM user_list
            WHERE usrlst_email = %s AND usrlst_password = SHA1(%s)
        """, (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        role = user.get("usrlst_role", "").lower()
        redirect_to = "/user/dashboard"
        if role == "admin":
            message = "Admin login successful"
            redirect_to = "/admin/dashboard"
        elif role == "user":
            message = "User login successful"
        else:
            message = "Login successful"

        response = {
            "message": message,
            "user": user,
            "redirect_to": redirect_to
        }

        if role == "admin":
            response["user_dashboard"] = "/user/dashboard"

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

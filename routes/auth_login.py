from flask import Blueprint, request, jsonify, session
from database import get_db_connection
from datetime import datetime
import bcrypt

login_bp = Blueprint('login_bp', __name__, url_prefix="/login")

# ---------------- LOGIN ----------------
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
            SELECT usrlst_id, usrlst_name, usrlst_email, usrlst_password,
                   usrlst_role, usrlst_department, usrlst_company_name
            FROM user_list
            WHERE usrlst_email = %s
        """, (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid email or password"}), 401

        stored_password = user['usrlst_password'].encode('utf-8')


        if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid email or password"}), 401

        #session
        session['user_id'] = user['usrlst_id']
        session['user_name'] = user['usrlst_name']
        session['user_email'] = user['usrlst_email']
        session['user_role'] = user['usrlst_role']
        session['user_department'] = user['usrlst_department']
        session['user_company'] = user['usrlst_company_name']

        #roles
        role = user.get("usrlst_role", "").lower()
        redirect_to = "/user/dashboard"
        if role == "admin":
            session["admin_id"] = user["usrlst_id"]
            message = "Admin login successful"
            redirect_to = "/admin/dashboard"
        elif role == "user":
            message = "User login successful"
        else:
            message = "Login successful"


        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')


        cursor.execute("""
            INSERT INTO activity_log (acty_department, acty_email, acty_date, acty_time, acty_action)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user['usrlst_department'],
            user['usrlst_email'],
            current_date,
            current_time,
            'Logged In'
        ))
        conn.commit()

        response = {
            "message": message,
            "user": {
                "id": user["usrlst_id"],
                "name": user["usrlst_name"],
                "email": user["usrlst_email"],
                "role": user["usrlst_role"],
                "department": user["usrlst_department"]
            },
            "redirect_to": redirect_to
        }

        cursor.close()
        conn.close()
        return jsonify(response), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



@login_bp.route('/logout', methods=['POST'])
def logout():
    try:
        user_email = session.get('user_email')
        user_department = session.get('user_department')

        if user_email:
            conn = get_db_connection()
            cursor = conn.cursor()

            current_date = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%H:%M:%S')

            #activity log
            cursor.execute("""
                INSERT INTO activity_log (acty_department, acty_email, acty_date, acty_time, acty_action)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_department,
                user_email,
                current_date,
                current_time,
                'Logged Out'
            ))
            conn.commit()
            cursor.close()
            conn.close()

        session.clear()
        return jsonify({"message": "Logged out successfully"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

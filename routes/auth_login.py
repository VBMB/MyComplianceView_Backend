from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from database import get_db_connection
from datetime import datetime
import bcrypt

#Change: Updated login and logout routes with improved error handling and logging.
#Changes made on 2026-01-22 by Sanskar Sharma.

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
            SELECT 
                usrlst_id,
                usrlst_name,
                usrlst_email,
                usrlst_password,
                usrlst_role,
                usrlst_department_id,
                usrlst_user_group_id,
                usrlst_login_flag
            FROM user_list
            WHERE usrlst_email = %s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid email or password"}), 401

        if str(user["usrlst_login_flag"]).strip() != "1":
            cursor.close()
            conn.close()
            return jsonify({"error": "User suspended"}), 403

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user["usrlst_password"].encode("utf-8")
        ):
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid email or password"}), 401

        token = create_access_token(
            identity=str(user["usrlst_id"]),
            additional_claims={
                "email": user["usrlst_email"],
                "role": user["usrlst_role"],
                "department_id": user["usrlst_department_id"],
                "user_group_id": user["usrlst_user_group_id"]
            }
        )

        role = (user["usrlst_role"] or "").lower()
        redirect_to = "/admin/dashboard" if role == "admin" else "/user/dashboard"
        message = "Admin login successful" if role == "admin" else "Login successful"

        cursor.execute("""
            SELECT usrdept_department_name
            FROM user_departments
            WHERE usrdept_id = %s
        """, (user["usrlst_department_id"],))

        dept_row = cursor.fetchone()
        department_name = dept_row["usrdept_department_name"] if dept_row else "Unknown Department"

        action_message = (
            f"User ID: {user['usrlst_id']} | "
            f"User Group ID: {user['usrlst_user_group_id']} | "
            f"Department: {department_name} | "
            f"Action: Logged In"
        )

        print("ACTION LOG:", action_message)

        cursor.execute("""
            INSERT INTO activity_log
            (
                acty_department,
                acty_email,
                acty_date,
                acty_time,
                acty_action,
                acty_user_group_id,
                acty_user_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            department_name,
            user["usrlst_email"],
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M:%S"),
            action_message,
            user["usrlst_user_group_id"],
            user["usrlst_id"]
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": message,
            "token": token,
            "user": {
                "usrlst_id": user["usrlst_id"],
                "usrlst_name": user["usrlst_name"],
                "usrlst_email": user["usrlst_email"],
                "usrlst_role": user["usrlst_role"],
                "usrlst_department_id": user["usrlst_department_id"],
                "usrlst_user_group_id": user["usrlst_user_group_id"]
            },
            "redirect_to": redirect_to
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- LOGOUT ----------------
# @login_bp.route('/logout', methods=['POST'])
# def logout():
#     try:
#         data = request.get_json() or {}
#         email = data.get("email")

#         if not email:
#             return jsonify({"error": "Email is required"}), 400

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             SELECT 
#                 usrlst_id,
#                 usrlst_email,
#                 usrlst_department_id,
#                 usrlst_user_group_id
#             FROM user_list
#             WHERE usrlst_email = %s
#         """, (email,))

#         user = cursor.fetchone()

#         if not user:
#             cursor.close()
#             conn.close()
#             return jsonify({"error": "User not found"}), 404

#         cursor.execute("""
#             SELECT usrdept_department_name
#             FROM user_departments
#             WHERE usrdept_id = %s
#         """, (user["usrlst_department_id"],))

#         dept_row = cursor.fetchone()
#         department_name = dept_row["usrdept_department_name"] if dept_row else "Unknown Department"

#         action_message = (
#             f"User ID: {user['usrlst_id']} | "
#             f"User Group ID: {user['usrlst_user_group_id']} | "
#             f"Department: {department_name} | "
#             f"Action: Logged Out"
#         )

#         cursor.execute("""
#             INSERT INTO activity_log
#             (
#                 acty_department,
#                 acty_email,
#                 acty_date,
#                 acty_time,
#                 acty_action,
#                 acty_user_group_id,
#                 acty_user_id
#             )
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#         """, (
#             department_name,
#             user["usrlst_email"],
#             datetime.now().strftime("%Y-%m-%d"),
#             datetime.now().strftime("%H:%M:%S"),
#             action_message,
#             user["usrlst_user_group_id"],
#             user["usrlst_id"]
#         ))

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"message": "Logged out successfully"}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
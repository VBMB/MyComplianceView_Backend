from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_db_connection
from datetime import datetime

logout_bp = Blueprint("logout_bp", __name__)

@logout_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()

        email = claims.get("email")
        department_id = claims.get("department_id")
        user_group_id = claims.get("user_group_id")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT usrdept_department_name
            FROM user_departments
            WHERE usrdept_id = %s
        """, (department_id,))

        dept_row = cursor.fetchone()
        department_name = dept_row["usrdept_department_name"] if dept_row else "Unknown Department"

        action_message = (
            f"User ID: {user_id} | "
            f"User Group ID: {user_group_id} | "
            f"Department: {department_name} | "
            f"Action: Logged Out"
        )

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
            email,
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M:%S"),
            action_message,
            user_group_id,
            user_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Logged out successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

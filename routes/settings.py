from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_db_connection
from utils.activity_logger import log_activity
import bcrypt

settings_bp = Blueprint(
    "settings_bp",
    __name__,
    url_prefix="/settings"
)

@settings_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    try:
        data = request.get_json()
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            return jsonify({
                "error": " password are required"
            }), 400

        if new_password != confirm_password:
            return jsonify({
                "error": "password do not match"
            }), 400

        if old_password == new_password:
            return jsonify({
                "error": "New password must be different from old password"
            }), 400


        user_id = get_jwt_identity()
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                u.usrlst_password,
                u.usrlst_email,
                d.usrdept_department_name AS department_name
            FROM user_list u
            JOIN user_departments d
                ON d.usrdept_id = u.usrlst_department_id
            WHERE u.usrlst_id = %s
        """, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User or department not found"}), 404

        if not bcrypt.checkpw(
            old_password.encode("utf-8"),
            user["usrlst_password"].encode("utf-8")
        ):
            return jsonify({"error": "Old password is incorrect"}), 401

        # if old_password == new_password:
        #     return jsonify({"error": "New password must be different"}), 400

        new_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute("""
            UPDATE user_list
            SET usrlst_password = %s
            WHERE usrlst_id = %s
        """, (new_hash, user_id))
        conn.commit()


        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department=user["department_name"],
            email=user["usrlst_email"],
            action="Password Changed"
        )

        cursor.close()
        conn.close()

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

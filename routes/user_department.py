from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from database import get_db_connection
from utils.activity_logger import log_activity

user_department_bp = Blueprint(
    "user_department_bp",
    __name__,
    url_prefix="/user/departments"
)

# --------------------------------------------------
# ADD DEPARTMENT (ADMIN ONLY)
# --------------------------------------------------
@user_department_bp.route("/add", methods=["POST"])
@jwt_required()
def add_department():
    claims = get_jwt()

    # ✅ Admin check
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}

    business_unit_id = data.get("business_unit_id")
    user_id = data.get("user_id")
    department_name = data.get("department_name")
    user_group_id = claims.get("user_group_id")

    if not all([business_unit_id, user_id, department_name]):
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "SELECT usrbu_id FROM user_business_unit WHERE usrbu_id=%s",
            (business_unit_id,)
        )
        if not cursor.fetchone():
            return jsonify({"error": "Business unit does not exist"}), 400

        # ✅ Validate user belongs to same group
        cursor.execute(
            "SELECT usrlst_id FROM user_list WHERE usrlst_id=%s AND usrlst_user_group_id=%s",
            (user_id, user_group_id)
        )
        if not cursor.fetchone():
            return jsonify({"error": "User not found in your group"}), 400

        # ✅ Insert department
        cursor.execute("""
            INSERT INTO user_departments (
                usrdept_business_unit_id,
                usrdept_user_id,
                usrdept_user_group_id,
                usrdept_department_name
            )
            VALUES (%s, %s, %s, %s)
        """, (business_unit_id, user_id, user_group_id, department_name))

        conn.commit()

        log_activity(
            user_id=admin_id,
            user_group_id=user_group_id,
            department=department_name,
            email=admin_email,
            action=f"Department Added ({department_name})"
        )

        return jsonify({"message": "Department added successfully"}), 201

    except Exception as e:
        conn.rollback()
        current_app.logger.exception("Add department failed")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------
# GET ALL DEPARTMENTS (ADMIN ONLY)
# --------------------------------------------------
@user_department_bp.route("/all", methods=["GET"])
@jwt_required()
def get_departments():
    claims = get_jwt()

    # ✅ Admin check
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    user_group_id = claims.get("user_group_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                ud.usrdept_id,
                ud.usrdept_department_name,
                ub.usrbu_business_unit_name,
                ul.usrlst_name AS user_name
            FROM user_departments ud
            JOIN user_business_unit ub
                ON ud.usrdept_business_unit_id = ub.usrbu_id
            JOIN user_list ul
                ON ud.usrdept_user_id = ul.usrlst_id
            WHERE ud.usrdept_user_group_id = %s
            ORDER BY ud.usrdept_id DESC
        """, (user_group_id,))

        rows = cursor.fetchall()

        return jsonify(rows), 200

    except Exception as e:
        current_app.logger.exception("Fetch departments failed")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

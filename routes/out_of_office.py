from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db_connection
from utils.activity_logger import log_activity

out_of_office_bp = Blueprint(
    "out_of_office_bp",
    __name__,
    url_prefix="/outofoffice"
)

#get alt email
@out_of_office_bp.route("/status", methods=["GET"])
@jwt_required()
def out_of_office_status():
    try:
        identity = get_jwt_identity()
        user_id = identity["user_id"] if isinstance(identity, dict) else identity

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT usrlst_alt_email
            FROM user_list
            WHERE usrlst_id = %s
        """, (user_id,))

        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and user["usrlst_alt_email"]:
            return jsonify({
                "is_out_of_office": True,
                "alternate_email": user["usrlst_alt_email"]
            }), 200

        return jsonify({
            "is_out_of_office": False,
            "alternate_email": None
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# add
@out_of_office_bp.route("/add", methods=["POST"])
@jwt_required()
def add_out_of_office():
    try:
        data = request.get_json()
        alternate_email = data.get("alternate_email")

        if not alternate_email:
            return jsonify({"error": "Alternate email is required"}), 400

        identity = get_jwt_identity()
        user_id = identity["user_id"] if isinstance(identity, dict) else identity

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                ul.usrlst_user_group_id,
                ul.usrlst_email,
                ud.usrdept_department_name AS department_name,
                ul.usrlst_alt_email
            FROM user_list ul
            LEFT JOIN user_departments ud
                ON ud.usrdept_id = ul.usrlst_department_id
            WHERE ul.usrlst_id = %s
        """, (user_id,))

        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user["usrlst_alt_email"]:
            return jsonify({
                "message": "Already out of office",
                "alternate_email": user["usrlst_alt_email"]
            }), 200

        cur.execute("""
            UPDATE user_list
            SET usrlst_alt_email = %s
            WHERE usrlst_id = %s
        """, (alternate_email, user_id))

        conn.commit()

        log_activity(
            user_id=user_id,
            user_group_id=user["usrlst_user_group_id"],
            department=user["department_name"],
            email=user["usrlst_email"],
            action=f"Out Of Office Enabled (Alternate Email: {alternate_email})"
        )

        cur.close()
        conn.close()

        return jsonify({
            "message": "Out of office enabled",
            "alternate_email": alternate_email
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#back in office
@out_of_office_bp.route("/remove", methods=["POST"])
@jwt_required()
def remove_out_of_office():
    try:
        identity = get_jwt_identity()
        user_id = identity["user_id"] if isinstance(identity, dict) else identity

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                ul.usrlst_user_group_id,
                ul.usrlst_email,
                ud.usrdept_department_name AS department_name,
                ul.usrlst_alt_email
            FROM user_list ul
            LEFT JOIN user_departments ud
                ON ud.usrdept_id = ul.usrlst_department_id
            WHERE ul.usrlst_id = %s
        """, (user_id,))

        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not user["usrlst_alt_email"]:
            return jsonify({"message": "Already back in office"}), 200

        cur.execute("""
            UPDATE user_list
            SET usrlst_alt_email = NULL
            WHERE usrlst_id = %s
        """, (user_id,))

        conn.commit()

        log_activity(
            user_id=user_id,
            user_group_id=user["usrlst_user_group_id"],
            department=user["department_name"],
            email=user["usrlst_email"],
            action="Back In Office (Alternate Email Removed)"
        )

        cur.close()
        conn.close()

        return jsonify({"message": "Back in office successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

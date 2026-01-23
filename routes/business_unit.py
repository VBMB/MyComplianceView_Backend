from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from database import get_db_connection

business_unit_bp = Blueprint(
    "business_unit_bp",
    __name__,
    url_prefix="/user/business_unit"
)

@business_unit_bp.route("/all", methods=["GET"])
@jwt_required()
def get_business_units():
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    user_group_id = claims.get("user_group_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                ub.usrbu_id,
                ub.usrbu_business_unit_name,
                ul.usrlst_name AS user_name
            FROM user_business_unit ub
            LEFT JOIN user_list ul
                ON ub.usrbu_user_id = ul.usrlst_id
            WHERE ub.usrbu_user_group_id = %s
            ORDER BY ub.usrbu_id DESC
        """, (user_group_id,))

        rows = cursor.fetchall()
        return jsonify(rows), 200

    except Exception as e:
        current_app.logger.exception("Fetch business units failed")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@business_unit_bp.route("/add", methods=["POST"])
@jwt_required()
def add_business_unit():
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}

    business_unit_name = data.get("business_unit_name")
    user_id = data.get("user_id")
    user_group_id = claims.get("user_group_id")

    if not business_unit_name or not user_id:
        return jsonify({"error": "Business unit name and user_id are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ✅ Validate user belongs to same group
        cursor.execute("""
            SELECT usrlst_id
            FROM user_list
            WHERE usrlst_id = %s AND usrlst_user_group_id = %s
        """, (user_id, user_group_id))

        if not cursor.fetchone():
            return jsonify({"error": "User not found in your group"}), 400

        # ✅ Prevent duplicate business unit
        cursor.execute("""
            SELECT 1
            FROM user_business_unit
            WHERE usrbu_user_id = %s
              AND usrbu_business_unit_name = %s
        """, (user_id, business_unit_name))

        if cursor.fetchone():
            return jsonify({"error": "Business unit already exists"}), 400

        # ✅ Insert
        cursor.execute("""
            INSERT INTO user_business_unit
            (usrbu_business_unit_name, usrbu_user_id, usrbu_user_group_id)
            VALUES (%s, %s, %s)
        """, (business_unit_name, user_id, user_group_id))

        conn.commit()
        return jsonify({"message": "Business unit added successfully"}), 201

    except Exception as e:
        conn.rollback()
        current_app.logger.exception("Add business unit failed")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@business_unit_bp.route("/edit", methods=["PUT"])
@jwt_required()
def edit_business_unit():
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}

    usrbu_id = data.get("usrbu_id")
    new_name = data.get("business_unit_name")
    user_group_id = claims.get("user_group_id")

    if not usrbu_id or not new_name:
        return jsonify({"error": "Business unit ID and new name required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ✅ Verify ownership
        cursor.execute("""
            SELECT 1
            FROM user_business_unit
            WHERE usrbu_id = %s AND usrbu_user_group_id = %s
        """, (usrbu_id, user_group_id))

        if not cursor.fetchone():
            return jsonify({"error": "Business unit not found"}), 404

        cursor.execute("""
            UPDATE user_business_unit
            SET usrbu_business_unit_name = %s
            WHERE usrbu_id = %s
        """, (new_name, usrbu_id))

        conn.commit()
        return jsonify({"message": "Business unit updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        current_app.logger.exception("Edit business unit failed")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

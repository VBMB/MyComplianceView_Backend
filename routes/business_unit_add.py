from flask import Blueprint, request, jsonify
from database import get_db_connection

business_unit_add_bp = Blueprint('business_unit_add_bp', __name__, url_prefix="/user/business_unit")

@business_unit_add_bp.route('/add', methods=['POST'])
def add_business_unit():
    data = request.get_json()
    business_unit_name = data.get("business_unit_name")
    user_id = data.get("user_id")
    user_group_id = data.get("user_group_id")

    if not business_unit_name or not user_id or not user_group_id:
        return jsonify({"error": "Business Unit Name, User ID, and User Group ID are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("SELECT * FROM user_list WHERE usrlst_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User ID does not exist"}), 400


        cursor.execute("""
            INSERT INTO user_business_unit
            (usrbu_business_unit_name, usrbu_user_id, usrbu_user_group_id)
            VALUES (%s, %s, %s)
        """, (business_unit_name, user_id, user_group_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Business Unit added successfully"}), 201

from flask import Blueprint, request, jsonify
from database import get_db_connection
import traceback

business_unit_add_bp = Blueprint('business_unit_add_bp', __name__, url_prefix="/user/business_unit")

@business_unit_add_bp.route('/add', methods=['POST'])
def add_business_unit():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    business_unit_name = data.get("business_unit_name")
    user_id = data.get("user_id")

    if not business_unit_name or not user_id:
        return jsonify({"error": "Business Unit Name and User ID are required"}), 400

   # try:
   #     user_id = int(user_id)
   # except ValueError:
   #     return jsonify({"error": "User ID must be an integer"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:

        cursor.execute("SELECT usrlst_user_group_id FROM user_list WHERE usrlst_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "User ID does not exist"}), 400


        if isinstance(result, dict):
            user_group_id = result.get('usrlst_user_group_id')
        else:
            user_group_id = result[0]

        if user_group_id is None:
            return jsonify({"error": "User group ID not found "}), 400


        cursor.execute("""
            SELECT 1 FROM user_business_unit
            WHERE usrbu_user_id = %s AND usrbu_business_unit_name = %s
        """, (user_id, business_unit_name))

        if cursor.fetchone():
            return jsonify({"error": "This Business Unit already exists for the user"}), 400


        cursor.execute("""
            INSERT INTO user_business_unit
            (usrbu_business_unit_name, usrbu_user_id, usrbu_user_group_id)
            VALUES (%s, %s, %s)
        """, (business_unit_name, user_id, user_group_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        #print(traceback.format_exc())
        return jsonify({
            "error": str(e),
    #    "details": traceback.format_exc()
        }), 500

    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Business Unit added successfully"}), 201


#updated
@business_unit_add_bp.route('/edit', methods=['PUT'])
def edit_business_unit():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    usrbu_id = data.get("usrbu_id")
    new_business_unit_name = data.get("business_unit_name")

    if not usrbu_id or not new_business_unit_name:
        return jsonify({"error": "Business Unit ID and new name are required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:

        cursor.execute("SELECT 1 FROM user_business_unit WHERE usrbu_id = %s", (usrbu_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Business Unit not found"}), 404


        cursor.execute("""
            UPDATE user_business_unit
            SET usrbu_business_unit_name = %s
            WHERE usrbu_id = %s
        """, (new_business_unit_name, usrbu_id))

        conn.commit()
        return jsonify({"message": "Business Unit updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()



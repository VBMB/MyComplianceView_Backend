from flask import Blueprint, request, jsonify
from database import get_db_connection

user_departments_all_bp = Blueprint('user_departments_all_bp', __name__, url_prefix="/user/departments")

@user_departments_all_bp.route('/all', methods=['GET'])
def get_departments():
    print("GET /user/departments/all called")
    user_id = request.args.get("user_id")  # frontend provides user_id

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ud.usrdept_id, ud.usrdept_department_name, 
                   ub.usrbu_business_unit_name, ul.usrlst_name AS user_name, ud.usrdept_user_group_id
            FROM user_departments ud
            JOIN user_business_unit ub ON ud.usrdept_business_unit_id = ub.usrbu_id
            JOIN user_list ul ON ud.usrdept_user_id = ul.usrlst_id
            WHERE ud.usrdept_user_id = %s
        """, (user_id,))
        rows = cursor.fetchall()
        print("Rows fetched:", rows)

        if not rows:
            return jsonify({"message": "No departments found for this user"}), 404

        return jsonify(rows), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

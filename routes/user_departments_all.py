from flask import Blueprint, request, jsonify, session
from database import get_db_connection

user_departments_all_bp = Blueprint('user_departments_all_bp', __name__, url_prefix="/user/departments")

@user_departments_all_bp.route('/all', methods=['GET'])
def get_departments():
    print("GET /user/departments/all called")


    admin_id = session.get("admin_id")
    if not admin_id:
        return jsonify({"error": "Unauthorized access. Please log in as admin."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        query = """
            SELECT 
                ud.usrdept_id, 
                ud.usrdept_department_name,
                ub.usrbu_business_unit_name,
                ul.usrlst_name AS user_name, 
                ud.usrdept_user_group_id
            FROM user_departments ud
            JOIN user_business_unit ub ON ud.usrdept_business_unit_id = ub.usrbu_id
            JOIN user_list ul ON ud.usrdept_user_id = ul.usrlst_id
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        print("Rows fetched:", rows)

        if not rows:
            return jsonify({"message": "No departments found."}), 404

        return jsonify(rows), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

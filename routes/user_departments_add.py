from flask import Blueprint, request, jsonify
from database import get_db_connection

user_departments_add_bp = Blueprint('user_departments_add_bp', __name__, url_prefix="/user/departments")

@user_departments_add_bp.route('/add', methods=['POST'])
def add_department():
    print("POST /user/departments/add called")
    data = request.get_json()
    print("Received JSON data:", data)

    business_unit_id = data.get("business_unit_id")
    user_id = data.get("user_id")
    user_group_id = data.get("user_group_id")
    department_name = data.get("department_name")

    if not business_unit_id or not user_id or not user_group_id or not department_name:
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("SELECT * FROM user_business_unit WHERE usrbu_id = %s", (business_unit_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Business Unit ID does not exist"}), 400


        cursor.execute("SELECT * FROM user_list WHERE usrlst_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User ID does not exist"}), 400


        cursor.execute("""
            SELECT * FROM user_departments 
            WHERE usrdept_business_unit_id = %s 
              AND usrdept_user_id = %s 
              AND usrdept_department_name = %s
        """, (business_unit_id, user_id, department_name))
        if cursor.fetchone():
            return jsonify({"error": "This department already exists"}), 400


        cursor.execute("""
            INSERT INTO user_departments
            (usrdept_business_unit_id, usrdept_user_id, usrdept_user_group_id, usrdept_department_name)
            VALUES (%s, %s, %s, %s)
        """, (business_unit_id, user_id, user_group_id, department_name))
        conn.commit()
        print(f"Inserted department: {department_name}")

    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Department added successfully"}), 201

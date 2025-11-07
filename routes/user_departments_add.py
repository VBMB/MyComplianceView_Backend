from flask import Blueprint, request, jsonify, session
from database import get_db_connection

# ✅ Unique blueprint name
user_departments_add_bp = Blueprint('user_departments_add_unique_bp', __name__, url_prefix="/user/departments")

@user_departments_add_bp.route('/add', methods=['POST'])
def add_department():
    print("POST /user/departments/add called")
    data = request.get_json()
    print("Received JSON data:", data)

    # get data
    business_unit_id = data.get("business_unit_id")
    user_id = data.get("user_id")
    user_group_id = data.get("user_group_id")
    department_name = data.get("department_name")


    if not all([business_unit_id, user_id, user_group_id, department_name]):
        return jsonify({"error": "All fields are required"}), 400

    # session
    admin_id = session.get("admin_id")
    if not admin_id:
        return jsonify({"error": "Unauthorized. Please log in as admin."}), 401


    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("SELECT usrbu_id FROM user_business_unit WHERE usrbu_id = %s", (business_unit_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Business Unit ID does not exist"}), 400


        cursor.execute("SELECT usrlst_id FROM user_list WHERE usrlst_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User ID does not exist"}), 400

        # secure
        cursor.execute("""
            INSERT INTO user_departments (
                usrdept_business_unit_id, 
                usrdept_user_id, 
                usrdept_user_group_id, 
                usrdept_department_name
            ) VALUES (%s, %s, %s, %s)
        """, (business_unit_id, user_id, user_group_id, department_name))

        conn.commit()
        print(f" department added '{department_name}' for user_id={user_id}")

        return jsonify({"message": "Department added successfully"}), 201

    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

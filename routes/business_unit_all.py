from flask import Blueprint, request, jsonify
from database import get_db_connection
import traceback


business_unit_all_bp = Blueprint('business_unit_all_bp', __name__, url_prefix="/user/business_unit")

@business_unit_all_bp.route('/all', methods=['GET'])
def get_business_units_by_user():
    print("GET /user/business_unit/all called")

    user_id = request.args.get("user_id")
    print("Received user_id:", user_id)

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("Database connection established")

        query = """
            SELECT ub.usrbu_id,
                   ub.usrbu_business_unit_name,
                   u.usrlst_name AS user_name,
                   ub.usrbu_user_group_id
            FROM user_business_unit AS ub
            LEFT JOIN user_list AS u ON ub.usrbu_user_id = u.usrlst_id
            WHERE ub.usrbu_user_id = %s
            ORDER BY ub.usrbu_id DESC
        """
        print("Running query with user_id:", user_id)
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        print("Rows fetched:", rows)

        if not rows:
            return jsonify({"message": "No business units found for this user"}), 404

        result = []
        for row in rows:
            result.append({
                "usrbu_id": row.get("usrbu_id"),
                "business_unit_name": row.get("usrbu_business_unit_name"),
                "user_name": row.get("user_name") or "Unknown User",
                "user_group_id": row.get("usrbu_user_group_id"),
            })

        print("Returning result:", result)
        return jsonify(result), 200

    except Exception as e:
        print("Error fetching business units")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            cursor.close()
            conn.close()
            print("Database connection closed")
        except:
            pass
from flask import Blueprint, request, jsonify, session
from database import get_db_connection
from datetime import datetime

user_update_bp = Blueprint('user_update_bp', __name__, url_prefix="/user_update")

@user_update_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:

        user_role = session.get('user_role')
        user_company = session.get('user_company')
        admin_email = session.get('user_email')

        if not user_role or user_role.lower() != 'admin':
            return jsonify({"error": "Unauthorized access — admin only"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        name = data.get("name")
        escalation_mail = data.get("escalation_mail")
        contact = data.get("contact")
        department = data.get("department")

        if not any([name, escalation_mail, contact, department]):
            return jsonify({"error": "No fields to update"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()


        cursor.execute("""
            SELECT * FROM user_list 
            WHERE usrlst_id = %s AND usrlst_company_name = %s
        """, (user_id, user_company))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found or not part of your company"}), 404


        fields = []
        values = []
        if name:
            fields.append("usrlst_name = %s")
            values.append(name)
        if escalation_mail:
            fields.append("usrlst_escalation_mail = %s")
            values.append(escalation_mail)
        if contact:
            fields.append("usrlst_contact = %s")
            values.append(contact)
        if department:
            fields.append("usrlst_department = %s")
            values.append(department)

        # Update last updated timestamp
        fields.append("usrlst_last_updated = %s")
        values.append(datetime.now())

        values.append(user_id)

        query = f"UPDATE user_list SET {', '.join(fields)} WHERE usrlst_id = %s"
        cursor.execute(query, tuple(values))
        conn.commit()


        cursor.execute("""
            SELECT usrlst_id, usrlst_name, usrlst_email, usrlst_contact, 
                   usrlst_department, usrlst_escalation_mail, usrlst_company_name, usrlst_last_updated
            FROM user_list
            WHERE usrlst_id = %s
        """, (user_id,))
        updated_user = cursor.fetchone()

        # Log admin action
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')

        cursor.execute("""
            INSERT INTO activity_log (acty_department, acty_email, acty_date, acty_time, acty_action)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            department or user['usrlst_department'],
            admin_email,
            current_date,
            current_time,
            f"Updated user {user['usrlst_name']} (ID {user_id})"
        ))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "User updated successfully",
            "updated_user": updated_user
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

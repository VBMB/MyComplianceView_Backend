from flask import Blueprint, jsonify, session
from database import get_db_connection
from datetime import datetime, timedelta

activity_log_bp = Blueprint('activity_log_bp', __name__, url_prefix="/activity_log")

@activity_log_bp.route('/', methods=['GET'])
def get_activity_logs():
    try:
        user_role = session.get('user_role')
        user_company = session.get('user_company')

        # Allow only admins
        if not user_role or user_role.lower() != 'admin':
            return jsonify({"error": "Unauthorized access — admin only"}), 403

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT usrlst_email
            FROM user_list
            WHERE usrlst_company_name = %s
        """, (user_company,))
        user_emails = [row['usrlst_email'] for row in cursor.fetchall()]

        if not user_emails:
            cursor.close()
            conn.close()
            return jsonify({"message": "No users found for this company"}), 404


        format_strings = ','.join(['%s'] * len(user_emails))
        query = f"""
            SELECT 
                a.acty_department,
                a.acty_email,
                a.acty_date,
                a.acty_time,
                a.acty_action,
                u.usrlst_name,
                u.usrlst_role,
                u.usrlst_company_name
            FROM activity_log as a
            JOIN user_list u ON a.acty_email = u.usrlst_email
            WHERE a.acty_email IN ({format_strings})
            ORDER BY a.acty_date DESC, a.acty_time DESC
        """
        cursor.execute(query, tuple(user_emails))
        activities = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert datetime/timedelta objects to string
        for activity in activities:
            for key, value in activity.items():
                if isinstance(value, (datetime, timedelta)):
                    activity[key] = str(value)

        return jsonify({"activities": activities}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

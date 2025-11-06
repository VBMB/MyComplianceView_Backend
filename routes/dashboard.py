from flask import Blueprint, jsonify, session, request
from database import get_db_connection

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix="/dashboard")

@dashboard_bp.route('/summary', methods=['GET'])
def dashboard_summary():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS total_compliances
            FROM compliance_list
            WHERE cmplst_user_id = %s
        """, (user_id,))
        total_compliances = cursor.fetchone()["total_compliances"]

        cursor.execute("""
            SELECT MAX(cmplst_end_date) AS subscription_end_date
            FROM compliance_list
            WHERE cmplst_user_id = %s
        """, (user_id,))
        subscription_end_date = cursor.fetchone()["subscription_end_date"]

        cursor.execute("""
            SELECT COUNT(*) AS total_departments
            FROM user_departments
        """)
        total_departments = cursor.fetchone()["total_departments"]

        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                    (TIMESTAMPDIFF(MONTH, cmplst_start_date, cmplst_end_date) + 1)
                    - COALESCE(cmplst_actions_completed, 0)
                ), 0) AS total_pending_actions
            FROM compliance_list
            WHERE cmplst_user_id = %s
        """, (user_id,))
        total_pending_actions = cursor.fetchone()["total_pending_actions"]

        cursor.close()
        conn.close()

        return jsonify({
            "total_compliances": total_compliances,
            "subscription_end_date": subscription_end_date,
            "total_departments": total_departments,
            "total_actions": total_pending_actions
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/mark_completed/<int:compliance_id>', methods=['POST'])
def mark_action_completed(compliance_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE compliance_list
            SET cmplst_actions_completed = COALESCE(cmplst_actions_completed, 0) + 1
            WHERE cmplst_id = %s AND cmplst_user_id = %s
        """, (compliance_id, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Action marked as completed"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

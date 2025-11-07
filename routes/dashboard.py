from flask import Blueprint, jsonify, session
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
            SELECT COUNT(*) AS total_departments
            FROM user_departments
            WHERE usrdept_user_id = %s
        """, (user_id,))
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

        cursor.execute("""
            SELECT g.usgrp_end_of_subscription
            FROM user_group g
            JOIN user_list u ON u.usrlst_user_group_id = g.usgrp_id
            WHERE u.usrlst_id = %s
        """, (user_id,))
        subscription_end = cursor.fetchone()
        subscription_end_date = None
        if subscription_end and subscription_end["usgrp_end_of_subscription"]:
            subscription_end_date = subscription_end["usgrp_end_of_subscription"].strftime("%d-%m-%Y")

        cursor.close()
        conn.close()

        return jsonify({
            "total_compliances": total_compliances,
            "total_departments": total_departments,
            "total_actions": total_pending_actions,
            "subscription_end_date": subscription_end_date
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_db_connection

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix="/dashboard")

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def dashboard_summary():
    try:
        # JWT identity is stored as STRING → convert to int
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")
        user_id = get_jwt_identity()

        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        if not user_group_id:
            return jsonify({"error": "User group not found"}), 401

        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"error": "Invalid user identity"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Total compliances
        # cursor.execute("""
        #     SELECT COUNT(*) AS total_compliances
        #     FROM compliance_list
        #     WHERE cmplst_user_id = %s
        # """, (user_id,))
        # total_compliances = cursor.fetchone()["total_compliances"]

        #Added by Sanskar Sharma to include both regulatory and self compliances
        cursor.execute("""
        SELECT 
        (
            SELECT COUNT(DISTINCT regcmp_compliance_id)
            FROM regulatory_compliance
            WHERE regcmp_user_id = %s
        ) +
        (
        SELECT COUNT(DISTINCT slfcmp_compliance_id)
        FROM self_compliance
        WHERE slfcmp_user_id = %s
        ) AS total_compliances
        """, (user_id, user_id))

        total_compliances = cursor.fetchone()["total_compliances"]

        # Total departments
        # cursor.execute("""
        #     SELECT COUNT(*) AS total_departments
        #     FROM user_departments
        #     WHERE usrdept_user_group_id = %s
        # """, (user_id,))
        # total_departments = cursor.fetchone()["total_departments"]

        cursor.execute("""
            SELECT COUNT(*) AS total_departments
            FROM user_departments
            WHERE usrdept_user_group_id = %s
        """, (user_group_id,))
        total_departments = cursor.fetchone()["total_departments"]

        # Pending actions
        # cursor.execute("""
        #     SELECT 
        #         COALESCE(SUM(
        #             (TIMESTAMPDIFF(MONTH, cmplst_start_date, cmplst_end_date) + 1)
        #             - COALESCE(cmplst_actions_completed, 0)
        #         ), 0) AS total_pending_actions
        #     FROM compliance_list
        #     WHERE cmplst_user_id = %s
        # """, (user_id,))
        # total_pending_actions = cursor.fetchone()["total_pending_actions"]

        # Subscription end date
        cursor.execute("""
            SELECT usgrp_end_of_subscription
            FROM user_group
            WHERE usgrp_id = %s
        """, (user_group_id,))

        row = cursor.fetchone()

        subscription_end_date = (
            row["usgrp_end_of_subscription"].strftime("%d-%m-%Y")
                if row and row.get("usgrp_end_of_subscription")
                    else None
        )

        cursor.close()
        conn.close()

        return jsonify({
            "total_compliances": total_compliances,
            "total_departments": total_departments,
            "subscription_end_date": subscription_end_date
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
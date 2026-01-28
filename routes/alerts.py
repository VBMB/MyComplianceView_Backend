from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import pymysql
from database import get_db_connection

alerts_bp = Blueprint("alerts_bp", __name__, url_prefix="/alerts")


@alerts_bp.route("/overdue", methods=["GET"])
@jwt_required()
def overdue_alerts():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")

        if not user_group_id:
            return jsonify({"error": "Unauthorized"}), 401

        user_group_id = int(user_group_id)

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                id,
                title,
                act,
                type,
                due_date,
                days_overdue
            FROM (
                SELECT
                    MIN(id) AS id,
                    title,
                    act,
                    type,
                    due_date,
                    MAX(days_overdue) AS days_overdue
                FROM (
                    -- Regulatory compliances
                    SELECT
                        regcmp_id AS id,
                        regcmp_particular AS title,
                        regcmp_act AS act,
                        'Regulatory' AS type,
                        regcmp_action_date AS due_date,
                        DATEDIFF(
                            CURDATE(),
                            STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')
                        ) AS days_overdue
                    FROM regulatory_compliance
                    WHERE
                        regcmp_user_group_id = %s
                        AND regcmp_status <> 'Approved'
                        AND STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()

                    UNION ALL

                    -- Self compliances
                    SELECT
                        slfcmp_id AS id,
                        slfcmp_particular AS title,
                        slfcmp_act AS act,
                        'Self' AS type,
                        slfcmp_action_date AS due_date,
                        DATEDIFF(
                            CURDATE(),
                            STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')
                        ) AS days_overdue
                    FROM self_compliance
                    WHERE
                        slfcmp_user_group_id = %s
                        AND slfcmp_status <> 'Approved'
                        AND STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                ) all_risk
                GROUP BY title, act, type, due_date
            ) final_risk
            ORDER BY days_overdue DESC
            LIMIT 5
        """, (
            user_group_id,
            user_group_id
        ))

        alerts = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "total_alerts": len(alerts),
            "alerts": alerts
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        user_group_id = int(claims.get("user_group_id"))

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                r.id,
                r.title,
                r.act,
                r.type,
                r.due_date,
                CASE
                    WHEN STR_TO_DATE(r.due_date, '%%d-%%m-%%Y') < CURDATE()
                        THEN 'HIGH_RISK'
                    WHEN STR_TO_DATE(r.due_date, '%%d-%%m-%%Y') = CURDATE()
                        THEN 'WARNING'
                END AS risk_level,
                DATEDIFF(
                    CURDATE(),
                    STR_TO_DATE(r.due_date, '%%d-%%m-%%Y')
                ) AS days_overdue
            FROM (
                SELECT
                    MIN(regcmp_id) AS id,
                    regcmp_particular AS title,
                    regcmp_act AS act,
                    'Regulatory' AS type,
                    regcmp_action_date AS due_date
                FROM regulatory_compliance
                WHERE
                    regcmp_user_group_id = %s
                    AND regcmp_status <> 'Approved'
                GROUP BY regcmp_particular, regcmp_act

                UNION ALL

                SELECT
                    MIN(slfcmp_id) AS id,
                    slfcmp_particular AS title,
                    slfcmp_act AS act,
                    'Self' AS type,
                    slfcmp_action_date AS due_date
                FROM self_compliance
                WHERE
                    slfcmp_user_group_id = %s
                    AND slfcmp_status <> 'Approved'
                GROUP BY slfcmp_particular, slfcmp_act
            ) r
            WHERE STR_TO_DATE(r.due_date, '%%d-%%m-%%Y') <= CURDATE()
            ORDER BY
                FIELD(risk_level, 'HIGH_RISK', 'WARNING'),
                days_overdue DESC
            LIMIT 5
        """, (user_group_id, user_group_id))

        alerts = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "total_alerts": len(alerts),
            "alerts": alerts
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

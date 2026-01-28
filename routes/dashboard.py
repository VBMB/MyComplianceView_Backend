from unittest import result
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_db_connection
import pymysql

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix="/dashboard")

#chnages made here
@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def dashboard_summary():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")
        user_id = get_jwt_identity()

        if not user_id or not user_group_id:
            return jsonify({"error": "Unauthorized"}), 401

        user_id = int(user_id)
        user_group_id = int(user_group_id)

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # --------------------------------------------------
        # TOTAL UNIQUE COMPLIANCES
        # --------------------------------------------------
        cursor.execute("""
            SELECT 
            (
                SELECT COUNT(DISTINCT regcmp_compliance_id)
                FROM regulatory_compliance
                WHERE regcmp_user_id = %s
                  AND regcmp_user_group_id = %s
            ) +
            (
                SELECT COUNT(DISTINCT slfcmp_compliance_id)
                FROM self_compliance
                WHERE slfcmp_user_id = %s
                  AND slfcmp_user_group_id = %s
            ) AS total_compliances
        """, (user_id, user_group_id, user_id, user_group_id))

        total_compliances = cursor.fetchone()["total_compliances"] or 0

        # --------------------------------------------------
        # TOTAL INSTANCES
        # --------------------------------------------------
        cursor.execute("""
            SELECT
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                ) AS regulatory_instances,
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ) AS self_instances
        """, (user_id, user_group_id, user_id, user_group_id))

        row = cursor.fetchone()
        regulatory_instances = row["regulatory_instances"] or 0
        self_instances = row["self_instances"] or 0
        total_instances = regulatory_instances + self_instances


        cursor.execute("""
            SELECT COUNT(*) AS total_departments
            FROM user_departments
            WHERE usrdept_user_group_id = %s
        """, (user_group_id,))
        total_departments = cursor.fetchone()["total_departments"] or 0

       
        cursor.execute("""
            SELECT usgrp_end_of_subscription
            FROM user_group
            WHERE usgrp_id = %s
        """, (user_group_id,))
        sub_row = cursor.fetchone()

        subscription_end_date = (
            sub_row["usgrp_end_of_subscription"].strftime("%d-%m-%Y")
            if sub_row and sub_row["usgrp_end_of_subscription"]
            else None
        )


        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved
            FROM (
                SELECT regcmp_status AS status
                FROM regulatory_compliance
                WHERE regcmp_user_id = %s
                  AND regcmp_user_group_id = %s
                UNION ALL
                SELECT slfcmp_status AS status
                FROM self_compliance
                WHERE slfcmp_user_id = %s
                  AND slfcmp_user_group_id = %s
            ) t
        """, (user_id, user_group_id, user_id, user_group_id))

        score = cursor.fetchone()
        compliance_score_percent = round(
            (score["approved"] / score["total"]) * 100, 2
        ) if score["total"] else 0

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status IN ('Pending', 'Requested')
                      AND regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status IN ('Pending', 'Requested')
                      AND slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ),
                0
            ) * 100 AS at_risk_percent
        """, (
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id
        ))

        at_risk_percent = round(cursor.fetchone()["at_risk_percent"] or 0, 2)
        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ),
                0
            ) * 100 AS low_risk_percent
        """, (
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id
        ))

        low_risk_percent = round(cursor.fetchone()["low_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ),
                0
            ) * 100 AS no_risk_percent
        """, (
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id
        ))

        no_risk_percent = round(cursor.fetchone()["no_risk_percent"] or 0, 2)

        cursor.close()
        conn.close()

        return jsonify({
            "compliance_score_percent": compliance_score_percent,

            "at_risk_percent": at_risk_percent,
            "low_risk_percent": low_risk_percent,
            "no_risk_percent": no_risk_percent,

            "total_compliances": total_compliances,
            "total_instances": total_instances,
            "regulatory_instances": regulatory_instances,
            "self_instances": self_instances,

            "total_departments": total_departments,
            "subscription_end_date": subscription_end_date
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#2step (up)
@dashboard_bp.route('/admin', methods=['GET'])
@jwt_required()
def dashboard_admin():
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
                COUNT(*) AS total_compliances,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_compliances
            FROM (
                SELECT regcmp_status AS status
                FROM regulatory_compliance
                WHERE regcmp_user_group_id = %s
                UNION ALL
                SELECT slfcmp_status AS status
                FROM self_compliance
                WHERE slfcmp_user_group_id = %s
            ) t
        """, (user_group_id, user_group_id))

        result = cursor.fetchone()
        total = result["total_compliances"] or 0
        approved = result["approved_compliances"] or 0
        compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status IN ('Pending','Requested')
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status IN ('Pending','Requested')
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*) FROM regulatory_compliance WHERE regcmp_user_group_id = %s
                ) +
                (
                    SELECT COUNT(*) FROM self_compliance WHERE slfcmp_user_group_id = %s
                ), 0
            ) * 100 AS at_risk_percent
        """, (user_group_id, user_group_id, user_group_id, user_group_id))

        at_risk_percent = round(cursor.fetchone()["at_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*) FROM regulatory_compliance WHERE regcmp_user_group_id = %s
                ) +
                (
                    SELECT COUNT(*) FROM self_compliance WHERE slfcmp_user_group_id = %s
                ), 0
            ) * 100 AS low_risk_percent
        """, (user_group_id, user_group_id, user_group_id, user_group_id))

        low_risk_percent = round(cursor.fetchone()["low_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*) FROM regulatory_compliance WHERE regcmp_user_group_id = %s
                ) +
                (
                    SELECT COUNT(*) FROM self_compliance WHERE slfcmp_user_group_id = %s
                ), 0
            ) * 100 AS no_risk_percent
        """, (user_group_id, user_group_id, user_group_id, user_group_id))

        no_risk_percent = round(cursor.fetchone()["no_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT *
            FROM (
                SELECT regcmp_id AS id, regcmp_act AS title,
                       regcmp_start_date AS start_date,
                       regcmp_end_date AS end_date,
                       'regulatory' AS type
                FROM regulatory_compliance
                WHERE regcmp_user_group_id = %s
                UNION ALL
                SELECT slfcmp_id AS id, slfcmp_act AS title,
                       slfcmp_start_date AS start_date,
                       slfcmp_end_date AS end_date,
                       'self' AS type
                FROM self_compliance
                WHERE slfcmp_user_group_id = %s
            ) t
            ORDER BY id DESC
            LIMIT 5
        """, (user_group_id, user_group_id))

        recent_compliances = cursor.fetchall()

        cursor.execute("""
            SELECT
                quarter_label,
                SUM(approved_count) OVER (ORDER BY quarter_num) AS approved_count,
                SUM(overdue_count) OVER (ORDER BY quarter_num) AS overdue_count
            FROM (
                SELECT
                    quarter_num,
                    CONCAT('Q', quarter_num) AS quarter_label,
                    COUNT(CASE WHEN status = 'Approved' THEN 1 END) AS approved_count,
                    COUNT(
                        CASE
                            WHEN status <> 'Approved'
                             AND action_date < CURDATE()
                        THEN 1 END
                    ) AS overdue_count
                FROM (
                    SELECT
                        STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') AS action_date,
                        regcmp_status AS status,
                        CASE
                            WHEN MONTH(STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 4 AND 6 THEN 1
                            WHEN MONTH(STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 7 AND 9 THEN 2
                            WHEN MONTH(STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 10 AND 12 THEN 3
                            ELSE 4
                        END AS quarter_num
                    FROM regulatory_compliance
                    WHERE regcmp_user_group_id = %s

                    UNION ALL

                    SELECT
                        STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') AS action_date,
                        slfcmp_status AS status,
                        CASE
                            WHEN MONTH(STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 4 AND 6 THEN 1
                            WHEN MONTH(STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 7 AND 9 THEN 2
                            WHEN MONTH(STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 10 AND 12 THEN 3
                            ELSE 4
                        END AS quarter_num
                    FROM self_compliance
                    WHERE slfcmp_user_group_id = %s
                ) base
                GROUP BY quarter_num
            ) q
            ORDER BY quarter_num
        """, (user_group_id, user_group_id))

        quarterly_compliance_track = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "group_id": user_group_id,
            "total_compliances": total,
            "approved_compliances": approved,
            "compliance_score_percent": compliance_score,
            "at_risk_percent": at_risk_percent,
            "low_risk_percent": low_risk_percent,
            "no_risk_percent": no_risk_percent,
            "recent_compliances": recent_compliances,
            "quarterly_compliance_track": quarterly_compliance_track
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/admin/act-status", methods=["GET"])
@jwt_required()
def act_status_summary():
    try:
        user_id = get_jwt().get("sub")

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT regcmp_act AS act, regcmp_status AS status
            FROM regulatory_compliance
            WHERE regcmp_user_id = %s
        """, (user_id,))
        regulatory = cursor.fetchall() or []

        cursor.execute("""
            SELECT slfcmp_act AS act, slfcmp_status AS status
            FROM self_compliance
            WHERE slfcmp_user_id = %s
        """, (user_id,))
        self_comp = cursor.fetchall() or []

        cursor.close()
        conn.close()

        all_rows = []
        all_rows.extend(list(regulatory))
        all_rows.extend(list(self_comp))

        act_status_map = {}

        for row in all_rows:
            act = row["act"]
            status = row["status"]

            if act not in act_status_map:
                act_status_map[act] = []

            act_status_map[act].append(status)

        completed = 0
        not_started = 0
        in_progress = 0

        act_details = []

        for act, statuses in act_status_map.items():
            unique_statuses = set(statuses)

            if unique_statuses == {"Approved"}:
                final_status = "Completed"
                completed += 1

            elif unique_statuses == {"Pending"}:
                final_status = "Not Started"
                not_started += 1

            else:
                final_status = "In Progress"
                in_progress += 1

            act_details.append({
                "act": act,
                "total_instances": len(statuses),
                "final_status": final_status
            })

        total_acts = len(act_status_map)

        completed_percentage = (
            round((completed / total_acts) * 100, 2)
            if total_acts > 0 else 0
        )

        return jsonify({
            "summary": {
                "completed": completed,
                "not_started": not_started,
                "in_progress": in_progress,
                "total_acts": total_acts,
                "completed_percentage": completed_percentage
            },
            "act_wise_data": act_details
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500